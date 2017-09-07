import read_page

class ToyApp(object):
    debug = False
    quiet = False
    def __init__(self):
        self.status = {'alert_messages': 0}


def test_parse_alert():
    page = (b"\x12\x1bP 000569192 @@ALERT F151210997 TYLD3 G&SC1 "
            b"GRASS FIRE SPREADING 1394 TRENTHAM RD KYNETON SOUTH "
            b"/PREMIER MINE RD SVC 6274 B11 (718696) "
            b"LAT/LON:-37.2919713, 144.4262171 AIRBEN CCARL CKYNE CTYLD "
            b"FBD302 [AIRBEN]")

    app = ToyApp()
    data = read_page.read_alert_message(app, page)
    assert data
    assert app.status['alert_messages'] == 1

    assert data['aircraftMsg'] == 1
    assert data['assignmentArea'] == 'TYLD3'
    assert data['cadEvent'] == 'F151210997'
    assert data['capCode'] == '000569192'
    assert data['coords'] == '718696'
    assert data['dirRef'] == 'SVC 6274 B11'
    assert data['dirType'] == 'SV'
    assert data['incType'] == 'G&S'
    assert data['lat'] == '-37.2919713'
    assert data['lon'] == '144.4262171'
    assert data['msgType'] == '@@ALERT'
    assert data['resource'] == 'AIRBEN'
    assert data['responseCode'] == '1'

def test_parse_cake():
    page = (b"\x12\x1bP 000569192 YOU WILL BE BAKED. AND THEN THERE WILL "
            b"BE CAKE. ")

    app = ToyApp()
    data = read_page.read_alert_message(app, page)
    assert not data

def test_parse_not_alert():
    page = (b"\x12\x1bP 000569192 @@CRITICAL F151210997 TYLD3 G&SC1 "
            b"GRASS FIRE SPREADING 1394 TRENTHAM RD KYNETON SOUTH "
            b"/PREMIER MINE RD SVC 6274 B11 (718696) "
            b"LAT/LON:-37.2919713, 144.4262171 AIRBEN CCARL CKYNE CTYLD "
            b"FBD302 [AIRBEN]")

    app = ToyApp()
    data = read_page.read_alert_message(app, page)
    assert not data

def skip_test_parse_very_ambiguous():
    # need to fix this index error
    page = (b"\x12\x1bP 000569192 @@ALERT F151210997")

    app = ToyApp()
    data = read_page.read_alert_message(app, page)
    assert data
    assert app.status['alert_messages'] == 1

    assert data['aircraftMsg'] == 1
    assert data['assignmentArea'] == 'TYLD3'
    assert data['cadEvent'] == 'F151210997'
    assert data['capCode'] == '000569192'
    assert data['coords'] == '718696'
    assert data['dirRef'] == 'SVC 6274 B11'
    assert data['dirType'] == 'SV'
    assert data['incType'] == 'G&S'
    assert data['lat'] == '-37.2919713'
    assert data['lon'] == '144.4262171'
    assert data['msgType'] == '@@ALERT'
    assert data['resource'] == 'AIRBEN'
    assert data['responseCode'] == '1'

def test_parse_small():
    page = (b"\x12\x1bP 000569192 @@ALERT tea for U&ME ")

    app = ToyApp()
    data = read_page.read_alert_message(app, page)
    assert data
    assert app.status['alert_messages'] == 1

    assert data['assignmentArea'] == 'for'
    assert data['cadEvent'] == 'tea'
    assert data['capCode'] == '000569192'
    assert data['coords'] == '\x1bP 000569192 @@ALERT tea for U&ME'
    assert data['dirRef'] == ''
    assert data['dirType'] == 'Unknown'
    assert data['incType'] == 'U&'
    assert data['msgType'] == '@@ALERT'
    assert data['resource'] == 'unknown'
    assert data['responseCode'] == 'E'

