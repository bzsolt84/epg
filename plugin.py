# Embedded file name: /usr/lib/enigma2/python/Plugins/Extensions/eXistenZUpdater/plugin.py
from Plugins.Plugin import PluginDescriptor
from enigma import *
from Screens.Standby import *
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Screens.Screen import Screen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Console import Console
import ServiceReference
import os
from time import sleep
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from string import Template
import gettext
from Components.config import config

pluginVersion = '2.6.1.10'
pluginPath = resolveFilename(SCOPE_PLUGINS, 'Extensions/eXistenZUpdater')

try:
    cat = gettext.translation('lang', pluginPath + '/po', [config.osd.language.getText()])
    _ = cat.gettext
except:
    _ = lambda str: str

class ListManager(Screen):
    # Frissített skin sárga gombbal, kék nélkül
    skin = Template('\n\t<screen position="center,center" size="600,125" title="Csatorna lista letöltés v${version}" > \n\n\t\t<widget name="id_cur" position="0,25" size="600,30" halign="center" font="Regular;20" />\n\n\t\t<widget name="id_new" position="0,50" size="600,30" halign="center" font="Regular;20" />\n\t\t<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/eXistenZUpdater/buttons/green.png" position="80,100" size="90,40" alphatest="on" />\n\t\t<widget name="key_green" position="110,92" zPosition="1" size="150,40" font="Regular;20" halign="left" valign="center" backgroundColor="transpBlack" transparent="1" />\n\t\t<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/eXistenZUpdater/buttons/yellow.png" position="320,100" size="90,40" alphatest="on" />\n\t\t<widget name="key_yellow" position="350,92" zPosition="1" size="150,40" font="Regular;20" halign="left" valign="center" backgroundColor="transpBlack" transparent="1" />\n\t</screen>').substitute(plugin=pluginPath, version=pluginVersion)

    def __init__(self, session):
        self.service = None
        Screen.__init__(self, session)
        self['key_green'] = Label(_('Letöltés'))
        self['key_yellow'] = Label(_('App frissítés'))
        self['id_cur'] = Label(_('Telepített verzió: N/A'))
        self['id_new'] = Label(_('Legfrissebb verzió: N/A'))
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {
            'cancel': self.Exit,
            'green': self.Green,
            'yellow': self.Yellow
        }, -1)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        os.system('rm -f /tmp/revision')
        import subprocess
        # Ping és letöltés SSL hiba nélkül
        os.system('wget --no-check-certificate -q -T 3 -P /tmp https://raw.githubusercontent.com/bzsolt84/epg/main/revision')
            
        if os.path.exists('/tmp/revision'):
            new_v = subprocess.getoutput('. /tmp/revision && echo $VER').strip()
            new_d = subprocess.getoutput('. /tmp/revision && echo $DATE').strip()
            self['id_new'].setText(_('Legfrissebb: ') + new_d + " (" + new_v + ")")
        else:
            self['id_new'].setText(_('Legfrissebb verzió: nem elérhető'))
            
        if os.path.exists('/etc/enigma2/revision'):
            cs_d = subprocess.getoutput('. /etc/enigma2/revision >/dev/null 2>&1 && echo $DATE').strip()
            self['id_cur'].setText(_('Telepített: ') + cs_d)

    def start(self):
        self.StatRefresh(_('Folyamat indítása...'))
        self.session.open(InstallWin)
        self.Timer = eTimer()
        if marker == '2':
            self.Timer.callback.append(self.prepare_settings)
        elif marker == '3':
            self.Timer.callback.append(self.app_update)
        self.Timer.start(100, True)

    def Green(self):
        global marker
        marker = '2'
        self.start()

    def Yellow(self):
        global marker
        marker = '3'
        self.start()

    def app_update(self):
        self.StatRefresh(_('Plugin frissítése...\nKérlek várj...'))
        cmd = "wget --no-check-certificate -q -O /usr/lib/enigma2/python/Plugins/Extensions/eXistenZUpdater/plugin.py https://raw.githubusercontent.com/bzsolt84/epg/main/plugin.py"
        os.system(cmd)
        os.system("sync")
        self.StatRefresh(_('Frissítés KÉSZ!\nIndítsd újra a GUI-t!'))

    def prepare_settings(self):
        self.StatRefresh(_('Lista letöltése...'))
        os.system('wget --no-check-certificate -q -T 10 -P /tmp https://raw.githubusercontent.com/bzsolt84/epg/main/csatlist.zip')
        if os.path.exists('/tmp/csatlist.zip'):
            os.system('mkdir -p /tmp/csatlist/ && unzip -o /tmp/csatlist.zip -d /tmp/csatlist/')
            self.installing_settings()
        else:
            self.StatRefresh(_('HIBA!\nLetöltés sikertelen!'))

    def installing_settings(self):
        self.StatRefresh(_('Fájlok másolása...'))
        os.system('rm -f /etc/enigma2/userbouquet* /etc/enigma2/bouquets*')
        os.system('cp -rf /tmp/csatlist/* /etc/enigma2/')
        if os.path.exists('/etc/enigma2/satellites.xml'):
            os.system('mv -f /etc/enigma2/satellites.xml /etc/tuxbox/satellites.xml')
        
        try:
            from enigma import eDVBDB
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
        except:
            os.system('wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 > /dev/null 2>&1 &')
        
        self.cleaning_tmp()

    def cleaning_tmp(self):
        os.system('rm -rf /tmp/revision /tmp/csatlist*')
        os.system('sync')
        self.StatRefresh(_('Frissítés KÉSZ!\nA lista megújult.'))

    def StatRefresh(self, what):
        with open('/tmp/status', 'w') as f:
            f.write(what)

    def Exit(self):
        if os.path.exists('/tmp/status'): os.system('rm -f /tmp/status')
        self.close()

class InstallWin(Screen):
    skin = """
        <screen title="Frissítés" position="center,center" size="600,160" backgroundColor="#20000000" flags="wfNoBorder">
            <eLabel position="0,0" size="600,160" zPosition="-1" backgroundColor="#20101010" />
            <widget name="status_text" position="20,20" size="560,120" font="Regular;28" halign="center" valign="center" transparent="1" foregroundColor="#ffffff" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["status_text"] = Label(_("Kapcsolódás..."))
        self.closeTimer = eTimer()
        self.monitorTimer = eTimer()
        self.monitorTimer.callback.append(self.checkStatusFile)
        self.monitorTimer.start(500, False)

    def checkStatusFile(self):
        if os.path.exists('/tmp/status'):
            try:
                with open('/tmp/status', 'r') as f:
                    szoveg = f.read().strip()
                    self["status_text"].setText(szoveg)
                    if "KÉSZ" in szoveg.upper() or "HIBA" in szoveg.upper():
                        self.monitorTimer.stop()
                        self.closeTimer.callback.append(self.close)
                        self.closeTimer.start(5000, True)
            except: pass

def main(session, **kwargs):
    session.open(ListManager)

def Plugins(**kwargs):
    return [PluginDescriptor(name='Csatorna lista frissítés', description='v2.6.2.0', where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main)]