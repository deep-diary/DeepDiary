# coding: utf-8
from PySide6.QtCore import QObject


class Translator(QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.text = self.tr('Text')
        self.view = self.tr('View')
        self.menus = self.tr('Menus & toolbars')
        self.icons = self.tr('Icons')
        self.layout = self.tr('Layout')
        self.dialogs = self.tr('Dialogs & flyouts')
        self.scroll = self.tr('Scrolling')
        self.material = self.tr('Material')
        self.dateTime = self.tr('Date & time')
        self.navigation = self.tr('Navigation')
        self.basicInput = self.tr('Basic input')
        self.statusInfo = self.tr('Status & info')
        self.price = self.tr("Price")
        
        # DeepWin 功能模块翻译
        self.memory = self.tr('记忆管理')
        self.device = self.tr('设备控制')
        self.resource = self.tr('资源与需求')
        self.settings = self.tr('设置')
        self.logs = self.tr('日志')
        
        # 记忆管理模块翻译
        self.memorySearch = self.tr('搜索记忆')
        self.memoryList = self.tr('记忆列表')
        self.memoryType = self.tr('记忆类型')
        self.memoryDate = self.tr('记忆日期')
        
        # 设备控制模块翻译
        self.deviceList = self.tr('设备列表')
        self.controlPanel = self.tr('控制面板')
        self.jointControl = self.tr('关节控制')
        self.commandConsole = self.tr('指令控制台')
        self.deviceStatus = self.tr('设备状态')
        self.deviceType = self.tr('设备类型')
        
        # 资源需求模块翻译
        self.resourceList = self.tr('资源列表')
        self.demandList = self.tr('需求列表')
        self.resourceType = self.tr('资源类型')
        self.resourceStatus = self.tr('资源状态')
        self.resourceUsage = self.tr('资源使用率')
        self.demandType = self.tr('需求类型')
        self.demandPriority = self.tr('需求优先级')
        self.demandStatus = self.tr('需求状态')
        self.addResource = self.tr('添加资源')
        self.addDemand = self.tr('添加需求')
        self.editResource = self.tr('编辑资源')
        self.editDemand = self.tr('编辑需求')
        self.deleteResource = self.tr('删除资源')
        self.deleteDemand = self.tr('删除需求')
        
        # 布局管理模块翻译
        self.layoutManager = self.tr('布局管理')
        self.saveLayout = self.tr('保存布局')
        self.loadLayout = self.tr('加载布局')
        self.addLayout = self.tr('添加布局')
        self.deleteLayout = self.tr('删除布局')
        self.layoutName = self.tr('布局名称')
        self.layoutType = self.tr('布局类型')
        self.layoutProperties = self.tr('布局属性')
        self.layoutChildren = self.tr('子布局')
        self.verticalLayout = self.tr('垂直布局')
        self.horizontalLayout = self.tr('水平布局')
        self.flowLayout = self.tr('流式布局')
        self.layoutSpacing = self.tr('间距')
        self.layoutMargins = self.tr('边距')