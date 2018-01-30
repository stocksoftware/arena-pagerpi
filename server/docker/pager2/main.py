from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource
from pager2.helpers import (startup_cap_check, view_cap_check, JINJA, config,
                            getarg)
from pager2.write import write_update, write_startup
from pager2.read import get_pagers, get_pager_cycle
from datetime import datetime
import logging
import traceback
import sys
import json
import os.path

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

# Successfully installed
#
# Automat-0.6.0 attrs-17.4.0 constantly-15.1.0 hyperlink-17.3.1
# incremental-17.5.0 twisted-17.9.0 zope.interface-4.4.3
# MarkupSafe-1.0 jinja2-2.10


class StartupPage(Resource, object):
    isLeaf = True
    def __init__(self, db):
        self.db = db
        super(StartupPage, self).__init__()

    def render_GET(self, request):
        view_cap_check(request.args.get('token', [''])[0])
        pagers = get_pagers(self.db)
        if getarg(request, 'json', False):
            result = {'pagers' : pagers}
            request.setHeader('Content-Type', 'application/json')
            return json.dumps(result, indent=2, default=str).encode('utf-8')
        else:
            template = JINJA.get_template('status.html')
            return template.render({'pagers' : pagers}).encode('utf-8')

    def render_POST(self, request):
        result = {
            'request' : 'message2',
            'commands' : [],
            'info' : [],
            'errors' : [],
        }
        request.setHeader('Content-Type', 'application/json')
        try:
            self.inner_post(result, request)
        except Exception as e:
            logging.exception(e.message)
            result['errors'].append(
                ''.join(traceback.format_exception_only(type(e), e)))
        return json.dumps(result, indent=2).encode('utf-8')

    def inner_post(self, result, request):
        with self.db.begin():
            startup_cap_check(getarg(request, 'token', ''))
            data = dict((name, getarg(request, name, ''))
                        for name in ["hostname", "ip_address", "revision"])
            result['key'] = write_startup(self.db, request.getClientIP(),
                                          data)


class ReportPage(Resource, object):
    isLeaf = True
    def __init__(self, db):
        self.db = db
        super(ReportPage, self).__init__()

    def render_POST(self, request):
        result = {
            'request' : 'message2',
            'commands' : [],
            'info' : [],
            'errors' : []
        }
        request.setHeader('Content-Type', 'application/json')
        try:
            self.inner_post(result, request)
        except Exception as e:
            logging.exception(e.message)
            result['errors'].append(
                ''.join(traceback.format_exception_only(type(e), e)))
        return json.dumps(result, indent=2).encode('utf-8')
        
    def get_json(self, request, name):
        data = getarg(request, name, '{}')
        return json.loads(data)

    def inner_post(self, result, request):
        # this system has in the past relied on the hostname; here we
        # use the pager_key as a capability token.
        pcid = get_pager_cycle(self.db,
                               getarg(request, 'status_key', ''))
        now = datetime.now()
        with self.db.begin():
            write_update(self.db, pcid,
                         self.get_json(request, 'report'),
                         self.get_json(request, 'errors'),
                         self.get_json(request, 'messages'))


class UpdatePage(Resource):
    isLeaf = True
    def render_POST(self, request):
        startup_cap_check(getarg(request, 'token', ''))
        try:
            with os.path.join(os.path.dirname(__file__), 'update.py') as f:
                script = f.read()
        except OSError:
            script = ''
        self.setHeader('Content-Type', 'application/json')
        result = {
            'script_id' : 'experimental-0.0-47-gee04f8c',
            'script' : script,
        }
        return json.dumps(result, indent=2)


def main():
    from sqlalchemy import create_engine
    from pager2.schema import metadata

    for x, y, z in os.walk(THIS_DIR):
        for y_ in y:
            print x + '/' + y_ + '/'
        for z_ in z:
            print x + '/' + z_

    if sys.argv[1:] and sys.argv[1].startswith('--local'):
        config.CAP_PATH = 'pager_config.json'

    if os.path.exists('/pager-data'):
        dbname = '/pager-data/pager.sqlite'
    else:
        dbname = os.path.join(THIS_DIR, 'pager-data', 'pager.sqlite')
    engine = create_engine("sqlite://" + dbname)
    metadata.create_all(engine)
    db = engine.connect()

    pg = Resource()
    pg.putChild('message2', ReportPage(db))
    pg.putChild('startup', StartupPage(db))
    pg.putChild('update', UpdatePage())

    root = Resource()
    root.putChild('pager', pg)
    factory = Site(root)
    reactor.listenTCP(8080, factory)
    reactor.run()

if __name__ == '__main__':
    main()
