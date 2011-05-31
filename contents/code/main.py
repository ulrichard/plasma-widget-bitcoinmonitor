#!/usr/bin/env python

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
from json import load, loads
from urllib2 import urlopen,URLError,build_opener,HTTPCookieProcessor
from time import time,localtime

url = ["http://deepbit.net/api/", "http://www.btcguild.com/api.php?api_key=", "https://mining.bitcoin.cz/accounts/profile/json/"]

class bitcoinmonitorApplet(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
        self.last_getrate=0
        self.update_interval=300 #5 minutes

    def init(self):
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        self.setHasConfigurationInterface(True)
        self.dialog = None
        cg = self.config()
        self.APIkey = cg.readEntry("APIkey", QString("")).toString()
        self.pool = cg.readEntry("pool", 0).toInt()[0]

        self.layout=QGraphicsLinearLayout(Qt.Horizontal, self.applet)
        self.applet.setLayout(self.layout)
        self.label=Plasma.Label(self.applet)
        self.label.setAlignment(Qt.AlignVCenter)

        svg=Plasma.Svg(self)
        icon_path=self.package().path()+"contents/icons/logo.svg"
        svg.setImagePath(icon_path)
        self.ttip_icon=QIcon(icon_path)
        self.icon=Plasma.SvgWidget(svg)
        self.icon.setPreferredSize(20,20)
        policy=QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        self.icon.setSizePolicy(policy)

        self.layout.addItem(self.icon)
        self.layout.setAlignment(self.icon,Qt.AlignCenter)
        self.layout.addItem(self.label)

        if self.APIkey != "":
            self.update_values()
        self.update()
        self.startTimer(30000) #30 seconds

    def showConfigurationInterface(self):
        windowTitle = str(self.applet.name()) + " Settings" #i18nc("@title:window", "%s Settings" % str(self.applet.name()))
        self.ui = uic.loadUi(self.package().filePath('ui', '../ui/settings_general.ui'), self.dialog)

        if self.dialog is None:
            self.dialog = KDialog(None)
            self.dialog.setWindowTitle(windowTitle)

            self.dialog.setMainWidget(self.ui)

            self.dialog.setButtons(KDialog.ButtonCodes(KDialog.ButtonCode(KDialog.Ok | KDialog.Cancel | KDialog.Apply)))
            self.dialog.showButton(KDialog.Apply, False)

            self.connect(self.dialog, SIGNAL("applyClicked()"), self, SLOT("configAccepted()"))
            self.connect(self.dialog, SIGNAL("okClicked()"), self, SLOT("configAccepted()"))

        self.ui.APIkey.setText(self.APIkey)
        self.ui.pool.setCurrentIndex (self.pool)

        self.dialog.show()
    @pyqtSignature("configAccepted()")
    def configAccepted(self):
        cg = self.config()
        self.APIkey=self.ui.APIkey.text()
        self.pool=self.ui.pool.currentIndex()
        cg.writeEntry("APIkey", self.APIkey)
        cg.writeEntry("pool", self.pool)
        self.update()
        self.emit(SIGNAL("configNeedsSaving()"))
        self.update_values()

    def timerEvent(self,event):
        if time() - self.last_getrate > self.update_interval:
            self.update_values()
        self.update()
    def setToolTip(self):
        last=localtime(self.last_getrate)
        ttip=Plasma.ToolTipContent()
        ttip.setMainText("Bitcoin monitor")
        if self.pool == 0:
            ttip.setSubText("<br />Confirmed rewards: <span style=\"color:green; font-weight: bold\">{0:.4f}</span> BTC\
                <br />Hashrate: <span style=\"color:blue; font-weight: bold\">{1:.1f}</span> MHash/s".format(
                    self.confirmed, self.hashrate))
        if self.pool == 1:
            ttip.setSubText("<br />Confirmed rewards: <span style=\"color:green; font-weight: bold\">{0:.4f}</span> BTC\
                <br />Unconfirmed rewards: <span style=\"color:orange; font-weight: bold\">{1:.4f}</span> BTC\
                <br />Estimated rewards: <span style=\"color:red; font-weight: bold\">{2:.4f}</span> BTC\
                <br />Hashrate: <span style=\"color:blue; font-weight: bold\">{3:.1f}</span> MHash/s".format(
                    self.confirmed, self.unconfirmed, self.estimated, self.hashrate))
        if self.pool == 2:
            ttip.setSubText("<br />Confirmed rewards: <span style=\"color:green; font-weight: bold\">{0:.4f}</span> BTC\
                <br />Unconfirmed rewards: <span style=\"color:orange; font-weight: bold\">{1:.4f}</span> BTC\
                <br />Estimated rewards: <span style=\"color:red; font-weight: bold\">{2:.4f}</span> BTC".format(
                    self.confirmed, self.unconfirmed, self.estimated))
        ttip.setAutohide(False)
        ttip.setImage(self.ttip_icon)
        Plasma.ToolTipManager.self().setContent(self.applet,ttip)
    @pyqtSignature("update_values()")
    def update_values(self):
        if self.get_data():
            self.setToolTip()
    def get_data(self):
        try:
            opener = build_opener(HTTPCookieProcessor())
            self.data=loads(opener.open(url[self.pool] + str(self.APIkey)).read())
        except URLError as exc:
            return False
        self.last_getrate=time()
        if self.pool == 0:
            self.confirmed=float(self.data["confirmed_reward"])
            self.hashrate=float(self.data["hashrate"])
        if self.pool == 1:
            self.confirmed=float(self.data["user"]["confirmed_rewards"])
            self.unconfirmed=float(self.data["user"]["unconfirmed_rewards"])
            self.estimated=float(self.data["user"]["estimated_rewards"])
            self.hashrate=0
            for worker in self.data["workers"]:
                self.hashrate+=float(self.data["workers"][worker]["hash_rate"])
        if self.pool == 2:
            self.confirmed=float(self.data["confirmed_reward"])
            self.unconfirmed=float(self.data["unconfirmed_reward"])
            self.estimated=float(self.data["estimated_reward"])
        self.label.setText("{0:.4f}".format(self.confirmed))
        self.adjustSize()
        return True

def CreateApplet(parent):
    return bitcoinmonitorApplet(parent)