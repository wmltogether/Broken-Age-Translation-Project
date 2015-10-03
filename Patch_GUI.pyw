#coding=utf-8
import wx
import wx._gdi
import logging
import logging.handlers
import os
import codecs
class wxGUI(wx.Frame):
    def OnClick_makepatch(self , event):
        from LibPCK import RebuildPCKBundle
        msg_0 = u"补丁安装中!"
        try:
            msg_0 = u"补丁安装完成!"
            RebuildPCKBundle('data.pck')
            RebuildPCKBundle('pdata.pck')
            dlg0=wx.MessageDialog(None, msg_0 ,u"破碎时光补丁工具",wx.OK)
            r=dlg0.ShowModal()
            dlg0.Destroy()
        except:
            msg_0 = u"补丁安装失败，请检查是否为破碎时光第二章!"
            dlg0=wx.MessageDialog(None, msg_0 ,u"破碎时光补丁工具",wx.OK)
            r=dlg0.ShowModal()
            dlg0.Destroy()
    def OnClick_extractPCK(self , event):
        from LibPCK import extract_pck
        msg_0 = u"解包文件中!"
        try:
            msg_0 = u"解包文件中!>>>完成!"
            self.button0.SetLabel(u"解包data.pck中")
            extract_pck('data.pck')
            self.button0.SetLabel(u"解包pdata.pck中")
            
            extract_pck('pdata.pck')
            self.button0.SetLabel(u"解包完毕")
            dlg0=wx.MessageDialog(None, msg_0 ,u"破碎时光补丁工具",wx.OK)
            r=dlg0.ShowModal()
            dlg0.Destroy()
        except:
            msg_0 = u"解包文件失败，请检查是否为破碎时光第二章!"
            dlg0=wx.MessageDialog(None, msg_0 ,u"破碎时光补丁工具",wx.OK)
            r=dlg0.ShowModal()
            dlg0.Destroy()
        
    def __init__(self, parent, title = u"破碎时光补丁工具"):
        LOG_FILE = 'logcat.log'
        handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5)
        fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
        formatter = logging.Formatter(fmt)   # 实例化formatter  
        handler.setFormatter(formatter)      # 为handler添加formatter  
  
        self.logger = logging.getLogger('logcat')    # 获取名为logcat的logger  
        self.logger.addHandler(handler)           # 为logger添加handler  
        self.logger.setLevel(logging.DEBUG)  

        frame = wx.Frame.__init__(self, parent, -1, title,pos=(150, 150), size=(500, 250))
        self.SetIcon(wx.Icon('icon.ico',wx.BITMAP_TYPE_ICO))
        panel = wx.Panel(self, -1)
        self.button0 = wx.Button(panel, -1, u"解包数据", pos=(50, 10))
        self.button = wx.Button(panel, -1, u"打补丁", pos=(50, 70))
        if not os.path.exists("data.pck"):
            wx.StaticText(panel,-1,u"checking...未找到data.pck,请将pck放入exe同目录",(150,10)).SetForegroundColour('red')
            self.button0.Enable(False)
        else:
            wx.StaticText(panel,-1,u"对data.pck进行解包",(150,10))
        if not os.path.exists("pdata.pck"):
            wx.StaticText(panel,-1,u"checking...未找到pdata.pck,请将pck放入exe同目录",(150,25)).SetForegroundColour('red')
            self.button0.Enable(False)
        else:
            wx.StaticText(panel,-1,u"对pdata.pck进行解包",(150,25))
        wx.StaticText(panel,-1,u"对data.pck和pdata.pck写入汉化补丁",(150,70))
        height=32
        weight=wx.NORMAL
        wx.StaticText(panel,-1,u"https://github.com/wmltogether",(100,180)).SetForegroundColour('blue')
        self.Bind(wx.EVT_BUTTON, self.OnClick_makepatch,self.button)
        self.Bind(wx.EVT_BUTTON, self.OnClick_extractPCK,self.button0)

        
        self.button.SetDefault()
        self.Show()

if __name__ == '__main__':
    app = wx.App(redirect=True)
    wxGUI(None)
    app.MainLoop()
