import time
import random
import re
import ctypes
from ctypes import wintypes
from ok import BaseTask, og, TaskDisabledException


def _inst_line(text: str, color: str = " ", *, bold: bool = False, indent: int = 0):
    content = f"{'&nbsp;' * (indent * 4)}{text}"
    if bold:
        content = f"<strong>{content}</strong>"
    return f'<span style="color:{color};">{content}</span>'

def _inst_gap():
    return '<span style="font-size:4px;">&nbsp;</span>'

INST = "<br>".join(
    [
        _inst_line("🤝功能说明：", bold = True),
        _inst_line("• 实现自动完成店长特供 1-1 [任意角色通用，暂不含『安魂曲+达芙蒂尔』]"),
        _inst_gap(),
        _inst_line("⭕优化及调整：", bold = True),
        _inst_line("新增：", bold = True),
        _inst_line("• 新增调试模式，可输出调试日志并保存异常截图"),
        _inst_gap(),
        _inst_line("👉使用方法：（暂停默认快捷键 “F9”）", bold = True),
        _inst_line("• 有无挂机流均可，但仍然推荐使用挂机流。"),
        _inst_line("• 确保游戏中出现可交互的 “店长特供” 字样。"),
        _inst_line("• 游戏窗口推荐16:9分辨率，但不支持1600*900。", "#FF5555", bold = True),
        _inst_line("• 不支持带鱼屏等超宽比例分辨率。", "#FF5555", bold = True),
        _inst_gap(),
        _inst_line("❗❗❗注意：", bold = True),
        _inst_line("• 反馈时请按以下格式留言详细信息（必要时可包含详细日志）", "#FF5555", bold = True),
        _inst_line("└─ 版本：（请填写……）『格式：verx.x.x，例如：ver3.3.4』"),
        _inst_line("└─ 游戏分辨率：（请填写……）『格式：全屏/窗口+具体分辨率，例如：窗口+1920*1080』"),
        _inst_line("└─ 反馈内容：（请填写……）"),
        _inst_line("└─ 复现方式：（请填写……）"),
        _inst_gap()
    ]
)


class StoreManagerTask(BaseTask):

    CONF_ROUNDS = "循环次数"
    CONF_REVENUE_MODE = "营业玩法"
    CONF_DEBUG_MODE = "调试模式"

    INFO_STAGE = "当前阶段"
    INFO_ENERGY = "都市活力"
    INFO_MODE = "营业玩法"
    INFO_TIME = "剩余和目标营业时间"
    INFO_STAR = "星星数量"
    INFO_ROUND = "轮次"
    INFO_SUCCESS = "成功次数"
    INFO_ERROR = "错误"

    REVENUE_MAX_TIME = 65 # 允许营业的最大时间

    POS_LEVEL_SELECT = (0.1458, 0.3843) # 1-1 关卡
    POS_START = (0.8734, 0.9343) # 开始营业
    POS_TAP = (0.0469, 0.4056) # 锤子
    POS_EXIT = (0.0219, 0.0463) # 通关退出
    POS_EXIT_RESTART = (0.3906, 0.7685) # 结算时退出
    POS_REWARD = (0.6214, 0.7833) # 结算时领取方斯
    POS_BREAD_1 = (0.0583, 0.9139) # 面包1
    POS_BREAD_2 = (0.3786, 0.9148) # 面包2
    POS_BREAD_MAKE_1 = (0.0583, 0.7407) # 面包1制作
    POS_BREAD_MAKE_2 = (0.3333, 0.7407) # 面包2制作
    POS_BREAD_ING_2 = (0.1135, 0.6019) # 面包配料2
    POS_BREAD_ING_3 = (0.2031, 0.6019) # 面包配料3
    POS_DESSERT = (0.5073, 0.9148) # 甜品
    POS_DES_MAKE = (0.6484, 0.9519) # 甜品制作
    POS_DES_ING_3 = (0.5417, 0.6019) # 甜品配料3

    TIME_BOX = {'x': 0.4802, 'y': 0.0556, 'to_x': 0.5458, 'to_y': 0.1019} # 当前剩余营业时间区域
    LEVEL_BOX = {'x': 0.0068, 'y': 0.1259, 'to_x': 0.1719, 'to_y': 0.9519} # 关卡区域
    CHECK_LEVEL_BOX = {'x': 0.7919, 'y': 0.0426, 'to_x': 0.9792, 'to_y': 0.0778} # 营业时核对关卡区域
    ENERGY_BOX = {'x': 0.8125, 'y': 0.0296, 'to_x': 0.9000, 'to_y': 0.0648} # 都市活力区域
    STAR_BOXES = [ # 营业时三星检测区域
        {'x': 0.9484, 'y': 0.1657, 'to_x': 0.9557, 'to_y': 0.1769},
        {'x': 0.9484, 'y': 0.2259, 'to_x': 0.9557, 'to_y': 0.2370},
        {'x': 0.9484, 'y': 0.2861, 'to_x': 0.9557, 'to_y': 0.2972}
    ]
    RESULT_STAR_BOXES = [ #结算时三星检测区域
        {'x': 0.4714, 'y': 0.2685, 'to_x': 0.4786, 'to_y': 0.2815},
        {'x': 0.4974, 'y': 0.2685, 'to_x': 0.5047, 'to_y': 0.2815},
        {'x': 0.5234, 'y': 0.2685, 'to_x': 0.5307, 'to_y': 0.2815}
    ]
    YELLOW_STAR_COLOR = {'r': (250, 255), 'g': (200, 220), 'b': (50, 80),} # 黄色星星颜色范围

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "店长特供 - ver3.3.5"
        self.description = "自动完成店长特供 1-1"
        self.instructions = INST
        self.capture_config = {
            'windows': {
                'exe': 'HTGame.exe',
                'hwnd_class': 'UnrealWindow',
                'interaction': 'NTEInteraction',
                'capture_method': 'WGC'
            }
        }

        self._hwnd = None # 缓存游戏窗口句柄
        # ===========================
        # 配置项
        self.default_config.update({
            self.CONF_ROUNDS: 0,
            self.CONF_REVENUE_MODE: "玩法1：挂机流（需白藏）",
            self.CONF_DEBUG_MODE: False,
        })

        self.config_description.update({
            self.CONF_ROUNDS: "默认0为无限循环，直至都市活力耗尽",
            self.CONF_DEBUG_MODE: "默认关闭，开启后将输出调试日志并保存异常截图"
        })

        self.config_type.update({
            self.CONF_REVENUE_MODE: {
                "type": "drop_down",
                "options": [
                    "玩法1：挂机流（需白藏）",
                    "玩法2：任意角色通用",
                ]
            },
        })


    # ---------------------------
    # 工具函数
    # ---------------------------
    # ===========================
    # • 输出工具
    # 日志信息
    def set_info(self, key, value):
        self.info_set(key, value)

    def init_info_panel(self):
        self.info_set(self.INFO_STAGE, " ")
        self.info_set(self.INFO_ENERGY, " ")
        self.info_set(self.INFO_MODE, " ")
        self.info_set(self.INFO_TIME, " ")
        self.info_set(self.INFO_STAR, "0")
        self.info_set(self.INFO_ROUND, " ")
        self.info_set(self.INFO_SUCCESS, "0")
        self.info_set(self.INFO_ERROR, " ")

    def init_info_round(self): # 重置缓存
        self._last_time_info = None
        self._last_star_info = None
        self._last_debug_star = None
        self.info_set(self.INFO_ENERGY, " ")
        self.info_set(self.INFO_TIME, " ")
        self.info_set(self.INFO_STAR, "0")
        self.info_set(self.INFO_ERROR, " ")

    def debug_log(self, msg):
        if not self.get_debug_mode():
            return
        self.log_info(f"[Debug] {msg}")

    # 截图信息
    def debug_screenshot(self, name):
        if not self.get_debug_mode():
            return
        self.screenshot(name = f"第{self.current_round:03d}轮_{name}")

    # ===========================

    # ===========================
    # • 窗口工具
    # 获取游戏窗口句柄
    # ---------------------------
    def get_hwnd(self):
        if self._hwnd:
            return self._hwnd

        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW("UnrealWindow", None)
        self._hwnd = hwnd
        return hwnd

    # 获取游戏窗口尺寸
    # ---------------------------
    def get_client_size(self):
        rect = wintypes.RECT()
        ctypes.windll.user32.GetClientRect(
           self.get_hwnd(),
           ctypes.byref(rect)
        )
        return (rect.right, rect.bottom)

    # ===========================

    # ===========================
    # • 加载配置
    # 获取循环次数
    # ---------------------------
    def get_round_count(self):
        try:
            return int(self.config.get(self.CONF_ROUNDS, 0))
        except:
            return 0

    # 获取营业玩法
    # ---------------------------
    def get_revenue_mode(self):
        return self.config.get(
            self.CONF_REVENUE_MODE,
            "玩法1：挂机流（需白藏）"
        )
    
    # 调试模式
    def get_debug_mode(self):
        return self.config.get(self.CONF_DEBUG_MODE)

    # ===========================

    # ===========================
    # • 输入工具
    # 鼠标滚轮滚动
    # 参数wheel_delta 正数 -> 向上滚动  负数 -> 向下滚动
    # ---------------------------
    def wheel_rel(self, wheel_pos, wheel_delta):
        hwnd = self.get_hwnd()
        user32 = ctypes.windll.user32
        # 临时抢占前台（关键）
        user32.SetForegroundWindow(hwnd)
        # 鼠标点击目标位置（关键）
        self.random_click(wheel_pos, 1)
        time.sleep(0.20)
        # 滚轮事件
        user32.mouse_event(0x0800, 0, 0, wheel_delta, 0)
        time.sleep(0.05)

    # 鼠标滚轮查找目标关卡
    # ---------------------------
    def wheel_until_stage(
        self,
        wheel_pos,
        target = '1-1 新品练习I', # 目标关卡
        max_try = 6 # 最大次数
    ):
        for attempt in range(max_try):
           self.set_info(self.INFO_STAGE, f"第{attempt + 1}次尝试滚动查询关卡")
           # ========= 1. 执行滚轮 =========
           self.wheel_rel(wheel_pos, wheel_delta = 8400) # 120为一格
           time.sleep(0.05) # 等待UI刷新
           found = False

           # ========= 2. OCR检测 =========
           for retry in range(2):
               time.sleep(0.10)
               matched = self.find_level()
               if matched:
                   self.set_info(self.INFO_STAGE, f"已识别到目标关卡：{target}")
                   found = True
                   self.sleep(0.2)
                   break
               
           # ========= 3. 找到目标 =========
           if found:
               self.set_info(self.INFO_STAGE, "进行滚动校正")
               self.wheel_rel(wheel_pos, wheel_delta = 8400)
               time.sleep(0.2)
               matched = self.find_level()
               if matched:
                   self.set_info(self.INFO_STAGE, "尝试选择目标关卡")
                   return True
               else:
                   self.set_info(self.INFO_STAGE, "校正失败，继续查询")
            
        self.set_info(self.INFO_ERROR, f"查询关卡失败: {target}")
        self.debug_screenshot("查询关卡失败")
        return False

    # 随机点击（防止固定坐标）
    # ---------------------------
    def random_click(
        self,
        pos, # 坐标位置
        click_times, # 点击次数
        offset_x = 0.0015,
        offset_y = 0.0015,
        down_time = 0.10,
    ):
        times = click_times
        for attempt in range(times):
            x, y = pos
            rand_x = random.uniform(-offset_x, offset_x)
            rand_y = random.uniform(-offset_y, offset_y)
            self.click(
                x + rand_x,
                y + rand_y,
                down_time = down_time
            )
            self.sleep(0.03)

    # 营业玩法（适配任意角色通用）
    # 营业玩法一：挂机流（需白藏）
    # ---------------------------
    def revenue_method_1(self):
        self.set_info(self.INFO_MODE, "玩法1：挂机流（需白藏）")
        revenue_deadline = time.time() + self.REVENUE_MAX_TIME # 设置营业的最大时间
        last_check = 0
        while time.time() < revenue_deadline:
            self.random_click(self.POS_TAP, 1) # 点击锤子
            now = time.time()

            # 每1秒检测一次三星
            if now - last_check > 1.0:
                last_check = now
                # 检测营业时三星
                if self.check_stars(self.STAR_BOXES, '当前'):
                    self.set_info(self.INFO_STAGE, "达成通关")
                    self.sleep(1.0)
                    return
            self.sleep(0.05)

        self.set_info(self.INFO_ERROR, "营业超时")
        self.debug_screenshot("玩法1_营业超时")

    # 营业玩法二：无白藏（任意角色通用）
    # ---------------------------
    def revenue_method_2(self):
        self.set_info(self.INFO_MODE, "玩法2：任意角色通用")
        self.sleep(3.0)

        # 等待营业开始
        if not self.wait_time(1, 58):
            self.set_info(self.INFO_ERROR, "目标时间检测异常")
            self.debug_screenshot("玩法2_营业未开始或时间检测异常")
            return

        self.sleep(0.3)
        self.random_click(self.POS_BREAD_2, 2) # 点击面包2食材
        self.sleep(0.3)
        self.random_click(self.POS_DESSERT, 2) # 点击甜品进行烘培
        self.sleep(1.0)
        self.random_click(self.POS_BREAD_MAKE_2, 2) # 面包2准备制作

        # 第一位顾客
        if not self.wait_time(1, 52):
            self.set_info(self.INFO_ERROR, "目标时间检测异常")
            self.debug_screenshot("玩法2_顾客1时间检测异常")
            return

        self.random_click(self.POS_BREAD_ING_3, 2) # 交付面包2商品
        self.sleep(0.3)
        self.random_click(self.POS_BREAD_1, 2) # 点击面包1食材
        self.sleep(0.3)
        self.random_click(self.POS_DES_MAKE, 2) # 甜品准备制作
    
        # 第二位顾客
        if not self.wait_time(1, 48):
            self.set_info(self.INFO_ERROR, "目标时间检测异常")
            self.debug_screenshot("玩法2_顾客2时间检测异常")
            return

        self.random_click(self.POS_DES_ING_3, 2) # 交付甜品商品
        self.sleep(0.3)  
        self.random_click(self.POS_BREAD_MAKE_1, 2) # 面包1准备制作
    
        # 第三位顾客
        if not self.wait_time(1, 41):
            self.set_info(self.INFO_ERROR, "目标时间检测异常")
            self.debug_screenshot("玩法2_顾客3时间检测异常")
            return

        self.random_click(self.POS_BREAD_ING_2, 2) # 交付面包1商品
        self.sleep(1.0)
        
        deadline = time.time() + 5
        while time.time() < deadline:
            if self.check_stars(self.STAR_BOXES, '当前'):
                self.set_info(self.INFO_STAGE, "达成通关")
                self.sleep(1.0)
                return
            self.sleep(0.5)
    
        self.set_info(self.INFO_ERROR, "未检测到三星")
        self.debug_screenshot("玩法2_未检测到三星")
        return
    
    # 退出营业
    # ---------------------------
    def exit_revenue(self, normal_exit=True):
        self.random_click(self.POS_EXIT, 1) # 点击退出营业
        self.set_info(self.INFO_STAGE, "退出营业")
        self.sleep(1.5)
        if not self.wait_ocr(match = ['挑战成功', '挑战失败'], time_out = 10):
            self.set_info(self.INFO_ERROR, "未进入结算界面")
            self.debug_screenshot("未进入结算页面")
            pass

        # 达成三星
        if normal_exit and self.check_stars(self.RESULT_STAR_BOXES, '结算'):
            self.random_click(self.POS_REWARD, 1) # 结算时领取方斯
            self.set_info(self.INFO_STAGE, "挑战成功，领取方斯")
            self.sleep(1.5)
            return True # 记录成功次数
        # 未三星
        else: # 不领方斯继续下一轮
            self.set_info(self.INFO_STAGE, "挑战失败或未三星，重新开始")
            self.random_click(self.POS_EXIT_RESTART, 1) # 结算时点击退出
            self.sleep(1.5)
            return False

    # ===========================

    # ===========================
    # • OCR工具
    # OCR文本标准化
    # ---------------------------
    def normalize_text(self, text):
        clean = (
            text.replace(' ', '')
                .replace('—', '-')
                .replace('=', '-')
                .replace('I', '1')
                .replace('l', '1')
                .replace('|', '1')
        )
        return clean

    # 等待指定时间出现
    # ---------------------------
    def wait_time(self, minute, second, tolerance = 2, timeout = 10):
        deadline = time.time() + timeout # 最大OCR识别时间
        target_total = minute * 60 + second

        while time.time() < deadline:
            ocr_result = self.ocr(**self.TIME_BOX)

            if not ocr_result:
                self.set_info(self.INFO_ERROR, "无时间结果")
                self.sleep(1.0)
                continue

            rest_time = ''.join(box.name for box in ocr_result)
            match = re.search(r'(\d+)分(\d+)秒', rest_time) # 提取数字
            
            if match:
                cur_min = int(match.group(1))
                cur_sec = int(match.group(2))
                cur_total = cur_min * 60 + cur_sec
                time_info = (
                    f"剩余时间：{cur_min}分{cur_sec}秒；"
                    f"目标时间：{minute}分{second}秒 ±{tolerance}秒"
                )
                if time_info != self._last_time_info:
                    self._last_time_info = time_info
                    self.set_info(self.INFO_TIME, time_info)

                if abs(cur_total - target_total) <= tolerance: # 匹配目标时间
                    return True
                self.sleep(0.2) # 降低OCR频率
            else:
                self.set_info(self.INFO_ERROR, "剩余营业时间检测异常")

        self.set_info(self.INFO_ERROR, "时间识别超时")
        self.sleep(1.0)
        return False

    # OCR检测目标关卡
    # ---------------------------
    def find_level(self):
        self.sleep(0.5) # 让OCR内容刷新
        ocr_result = self.ocr(**self.LEVEL_BOX)
        texts = [box.name for box in ocr_result] if ocr_result else []

        if texts:
            #if self.get_debug_mode(): # Debug日志：查看OCR的原始关卡信息
            #    self.log_debug(f"OCR原始内容：{' | '.join(texts)}")
            #    self.sleep(3.0)

            for text in texts: # 逐行判断
                clean = self.normalize_text(text)
                #if self.get_debug_mode(): # Debug日志：查看每行OCR的关卡信息
                #    self.log_info(f"OCR标准化行内容：{clean}")
                #    self.sleep(1.0)

                # 目标关卡匹配
                if ("1-1" in clean and "新品练习" in clean):
                    self.set_info(self.INFO_STAGE, "检测到目标关卡")
                    time.sleep(0.5)
                    return True
        return False
    
    # 核对目标关卡
    # ---------------------------
    def check_level(self):
        ocr_result = self.ocr(**self.CHECK_LEVEL_BOX)
        if not ocr_result:
            self.set_info(self.INFO_ERROR, "营业时核对目标关卡异常，暂不处理")
            return True
        
        clean = self.normalize_text(ocr_result[0].name)
        if ("1-1" in clean and "新品练习" in clean):
            self.set_info(self.INFO_STAGE, f"进入关卡：{clean}")
            self.sleep(0.5)
            return True
        else:
            self.set_info(self.INFO_STAGE, f"误进关卡：{clean}，准备退出")
            self.sleep(4.0)
            self.exit_revenue(normal_exit=False)
            return False

    # 检测当前都市活力剩余值
    # ---------------------------
    def check_energy(self):
        energy = self.ocr(**self.ENERGY_BOX)
        self.set_info(self.INFO_STAGE, "检测都市活力剩余值")

        if not energy:
            self.set_info(self.INFO_ERROR, "未识别到都市活力")
            return True

        for box in energy:
            text = box.name
            self.set_info(self.INFO_ENERGY, text)

            if text.startswith('0/'):
                self.set_info(self.INFO_STAGE, "都市活力耗尽")
                return True
            
        return False

    # 检测是否达成三星
    # ---------------------------
    def check_stars(self, star_boxes, stage_name):
        num = 0
        debug_percent = []
        for star in star_boxes:
            star_box = self.box_of_screen(**star, name = stage_name)

            percent = self.calculate_color_percentage(
                self.YELLOW_STAR_COLOR,
                star_box
            )
            debug_percent.append(f"{percent:.3f}")
            if percent > 0.1:
                num += 1
        
        debug_star = (stage_name, num)
        if self.get_debug_mode() and debug_star != self._last_debug_star:
            self._last_debug_star = debug_star
            self.log_info(
                f"[Debug] {stage_name} "
                f"星1={debug_percent[0]} "
                f"星2={debug_percent[1]} "
                f"星3={debug_percent[2]} "
                f"-> {num}/3"
            )
        
        star_info = f"{stage_name}: {num}/3"
        if star_info != self._last_star_info:
            self._last_star_info = star_info
            self.set_info(self.INFO_STAR, star_info)
        
        return num >= 3

    # ===========================

    # ===========================
    # • 异常工具
    # 异常处理
    # ---------------------------
    def handle_exception(self, e):
        self.set_info(self.INFO_ERROR, f"店长特供执行异常: {e}")
        self.set_info(self.INFO_STAGE, "异常终止")
        self.sleep(2.0)

    # ===========================


    # ========================================
    # 店长特供任务（主逻辑）
    # ========================================
    def store_manager(self):
        # 步骤1：开始店长特供（按 F 进入店长特供）
        self.set_info(self.INFO_STAGE, "开始店长特供")
        if not self.wait_ocr(match = '店长特供', time_out = 10):
            self.set_info(self.INFO_ERROR, "未检测到店长特供")
            return

        self.sleep(0.5)
        entered = False
        enter_deadline = time.time() + 2.0 # 设置进入店长特供的超时时间
        while time.time() < enter_deadline:
            self.send_key('f', down_time = 0.10)
            if self.ocr(match = '开始营业'):
                entered = True
                break

        if not entered:
            self.set_info(self.INFO_ERROR, "进入店长特供超时")
            return

        # 步骤2：检测都市活力是否耗尽
        if self.check_energy():
            return "energy_empty"
        self.sleep(1.0)
        # 步骤3：滚轮滚动选择目标关卡
        if not self.wheel_until_stage(
            wheel_pos = self.POS_LEVEL_SELECT,
            target = '1-1 新品练习I'
        ):
            return

        self.sleep(1.0)
        self.random_click(self.POS_LEVEL_SELECT, 1) # 点击关卡 1-1
        self.sleep(0.5)
        # 步骤4：开始营业
        if not self.wait_ocr(match = '开始营业', time_out = 10):
            self.set_info(self.INFO_ERROR, "未检测到开始营业UI")
            return
        self.random_click(self.POS_START, 1) # 点击开始营业
        self.sleep(3.0)

        if not self.check_level(): # 核对目标关卡
            return # 未进入目标关卡重新开始
        self.set_info(self.INFO_STAGE, "营业中")
        self.sleep(0.5)
        # 步骤5：匹配营业玩法
        mode = self.get_revenue_mode()
        methods = {
            "玩法1": self.revenue_method_1,
            "玩法2": self.revenue_method_2,
        }
        for key, func in methods.items():
            if key in mode:
                func()
                break
        else:
            self.set_info(self.INFO_ERROR, f"未知营业玩法：{mode}")
        # 步骤6：营业结算
        return self.exit_revenue()


    # ========================================
    # 主函数入口
    # ========================================
    def run(self):
        self.init_info_panel()
        total_rounds = self.get_round_count()
        endless = total_rounds == 0 # 0表示无限循环
        current_round = 0 # 轮次
        success_count = 0 # 成功次数

        while endless or current_round < total_rounds:
            current_round += 1
            self.current_round = current_round
            self.init_info_round() # 重置信息面板缓存
            if endless:
                self.set_info(self.INFO_ROUND, f"{current_round}/∞")
            else:
                self.set_info(self.INFO_ROUND, f"{current_round}/{total_rounds}")

            try:
                task_result = self.store_manager()
                if task_result == "energy_empty":
                    self.set_info(self.INFO_STAGE, "都市活力耗尽，任务结束")
                    return
                elif task_result is True:
                    success_count += 1
                    self.set_info(self.INFO_SUCCESS, str(success_count))

            except TaskDisabledException:
                self.set_info(self.INFO_STAGE, "用户停止，任务结束")
                return

            except Exception as e:
                self.handle_exception(e)
        # 达到循环次数后
        self.set_info(self.INFO_STAGE, "已达目标轮次，任务结束")
