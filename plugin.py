# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
import os
import sys
import gettext
import ssl

# Enigma2 importok
from enigma import eDVBDB, eTimer
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from string import Template

# Python 2/3 hibrid hálózati import
if sys.version_info[0] < 3:
    import urllib2 as urllib
else:
    import urllib.request as urllib

pluginVersion = '2.6.2.16 hybrid'
pluginPath = resolveFilename(SCOPE_PLUGINS, 'Extensions/eXistenZUpdater')
marker = '0'

def decode_str(txt):
    if sys.version_info[0] >= 3:
        return txt.decode('utf-8') if isinstance(txt, bytes) else txt
    try: return txt.encode('utf-8') if isinstance(txt, unicode) else str(txt)
    except: return str(txt)

def download_internal(url, target):
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.urlopen(url, context=ctx, timeout=15)
        with open(target, 'wb') as f:
            f.write(req.read())
        return True
    except:
        res = os.system('wget --no-check-certificate -q "%s" -O %s' % (url, target))
        return res == 0 and os.path.exists(target) and os.path.getsize(target) > 0

class ListManager(Screen):
    # Kék gomb elrejtve a skinből, de a logikában benne marad
    skin = Template("""
    <screen position="center,center" size="600,150" title="Csatornalista Frissítő v${version}" > 
        <widget name="id_cur" position="0,20" size="600,30" halign="center" font="Regular;20" />
        <widget name="id_new" position="0,55" size="600,30" halign="center" font="Regular;20" />
        
        <ePixmap pixmap="${plugin}/buttons/green.png" position="80,110" size="30,30" alphatest="on" />
        <widget name="key_green" position="120,110" zPosition="1" size="150,30" font="Regular;20" halign="left" transparent="1" />
        
        <ePixmap pixmap="${plugin}/buttons/yellow.png" position="320,110" size="30,30" alphatest="on" />
        <widget name="key_yellow" position="360,110" zPosition="1" size="150,30" font="Regular;20" halign="left" transparent="1" />
    </screen>""").substitute(plugin=pluginPath, version=pluginVersion)

    def __init__(self, session):
        Screen.__init__(self, session)
        self['key_green'] = Label('Letöltés')
        self['key_yellow'] = Label('App frissítés')
        self['id_cur'] = Label('Telepített: ...')
        self['id_new'] = Label('Legfrissebb: ...')
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {
            'cancel': self.Exit,
            'green': self.Green,
            'yellow': self.Yellow,
            'blue': self.Blue # A gomb funkciója megmarad
        }, -1)
        
        self.initTimer = eTimer()
        try: self.initTimer_conn = self.initTimer.timeout.connect(self.layoutFinished)
        except: self.initTimer.callback.append(self.layoutFinished)
        self.initTimer.start(1000, True)

    def layoutFinished(self):
        url = 'https://raw.githubusercontent.com/bzsolt84/epg/main/revision'
        target = '/tmp/revision'
        if download_internal(url, target):
            try:
                with open(target, 'r') as f:
                    content = f.read().splitlines()
                    v, d = "N/A", "N/A"
                    for line in content:
                        if 'VER=' in line: v = line.split('=')[1].replace('"', '')
                        if 'DATE=' in line: d = line.split('=')[1].replace('"', '')
                self['id_new'].setText('Legfrissebb: ' + d + " (" + v + ")")
            except: self['id_new'].setText('Legfrissebb: Beolvasási hiba')
        else: self['id_new'].setText('Legfrissebb: GitHub elérés hiba')
        
        if os.path.exists('/etc/enigma2/revision'):
            try:
                with open('/etc/enigma2/revision', 'r') as f:
                    content = f.read().splitlines()
                    cv, cd = "N/A", "N/A"
                    for line in content:
                        if 'VER=' in line: cv = line.split('=')[1].replace('"', '')
                        if 'DATE=' in line: cd = line.split('=')[1].replace('"', '')
                self['id_cur'].setText('Telepített: ' + cd + " (" + cv + ")")
            except: pass

    def Green(self):
        global marker
        marker = '2'
        self.start_work()

    def Yellow(self):
        global marker
        marker = '3'
        self.start_work()
        
    def Blue(self):
        global marker
        marker = '4'
        self.start_work()

    def start_work(self):
        self.session.open(InstallWin)
        self.WorkTimer = eTimer()
        f = self.prepare_settings
        if marker == '3': f = self.app_update
        try: self.WorkTimer_conn = self.WorkTimer.timeout.connect(f)
        except: self.WorkTimer.callback.append(f)
        self.WorkTimer.start(1000, True)

    def prepare_settings(self):
        global marker
        self.StatRefresh('Lista letöltése...')
        url = 'https://raw.githubusercontent.com/bzsolt84/epg/main/csatlist.zip'
        if marker == '4':
            url = 'https://raw.githubusercontent.com/bzsolt84/epg/main/csatlist2.zip'
            self.StatRefresh('Alternatív lista...')
        
        if download_internal(url, '/tmp/csatlist.zip'):
            self.StatRefresh('Kicsomagolás...')
            os.system('rm -rf /tmp/csatlist && mkdir -p /tmp/csatlist/ && unzip -o /tmp/csatlist.zip -d /tmp/csatlist/')
            self.installing_settings()
        else: self.StatRefresh('HIBA!\nLetöltési hiba!')

    def app_update(self):
        self.StatRefresh('Plugin frissítése...')
        if download_internal('https://raw.githubusercontent.com/bzsolt84/epg/main/plugin.py', pluginPath + '/plugin.py'):
            os.system("sync")
            self.StatRefresh('KÉSZ!\nIndíts újra a kezelöfelületet (GUI)!')
        else: self.StatRefresh('HIBA!\nFrissítés sikertelen!')

    def installing_settings(self):
        self.StatRefresh('Másolás...')
        os.system('rm -f /etc/enigma2/userbouquet* /etc/enigma2/bouquets*')
        os.system('cp -rf /tmp/csatlist/* /etc/enigma2/')
        if os.path.exists('/etc/enigma2/satellites.xml'):
            os.system('mv -f /etc/enigma2/satellites.xml /etc/tuxbox/satellites.xml')
        try:
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
        except: os.system('wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /dev/null 2>&1 &')
        os.system('rm -rf /tmp/revision /tmp/csatlist*')
        self.StatRefresh('Frissítés KÉSZ!')

    def StatRefresh(self, what):
        try:
            with open('/tmp/status', 'w') as f: f.write(decode_str(what))
        except: pass

    def Exit(self):
        if os.path.exists('/tmp/status'): os.system('rm -f /tmp/status')
        self.close()

class InstallWin(Screen):
    skin = """<screen title="Frissítés" position="center,center" size="600,160" flags="wfNoBorder"><widget name="status_text" position="20,20" size="560,120" font="Regular;28" halign="center" valign="center" /></screen>"""
    def __init__(self, session):
        Screen.__init__(self, session)
        self["status_text"] = Label("Várj...")
        self.monitorTimer = eTimer()
        try: self.monitorTimer_conn = self.monitorTimer.timeout.connect(self.checkStatusFile)
        except: self.monitorTimer.callback.append(self.checkStatusFile)
        self.monitorTimer.start(500, False)

    def checkStatusFile(self):
        if os.path.exists('/tmp/status'):
            try:
                with open('/tmp/status', 'r') as f:
                    txt = f.read().strip()
                    self["status_text"].setText(txt)
                    if "KÉSZ" in txt.upper() or "HIBA" in txt.upper():
                        self.monitorTimer.stop()
                        self.closeTimer = eTimer()
                        try: self.closeTimer_conn = self.closeTimer.timeout.connect(self.close)
                        except: self.closeTimer.callback.append(self.close)
                        self.closeTimer.start(3000, True)
            except: pass

def main(session, **kwargs): session.open(ListManager)
def Plugins(**kwargs): return [PluginDescriptor(name='Csatornalista Frissítő', description='Csatornalista Frissítő v' + pluginVersion, where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main)]