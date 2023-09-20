from nakuru.entities.components import *
from nakuru import (
    GroupMessage,
    FriendMessage
)
from botpy.message import Message, DirectMessage
import random
import traceback
from .Life import Life,HandlerException
from model.platform.qq import QQ

class liferestartPlugin:
    def __init__(self) -> None:
        print("Remake :)")
        # 本脚本绝对路径
        self.path = os.path.dirname(os.path.abspath(__file__))
        Life.load(self.path + '/data')
        self.gamestart = False
        self.gamestate = None
        self.session = []
        self.group_id = None
        self.life = None
        self.run_life_ret = None
        self.qq_platform = None

    def run(self, message: str, role: str, platform: str, message_obj, qq_platform: QQ):
        if message_obj.type == "GroupMessage" and (message_obj.group_id == 703693608 or message_obj.group_id == 322154837):
            if message == "重开":
                self.qq_platform = qq_platform
                self.group_id = message_obj.group_id
                self.life = Life()
                run_life_ret, text = self.run_life()
                self.run_life_ret = run_life_ret
                self.gamestart = True
                text += '\n输入1继续。输入结束/stop/exit来结束游戏.\n\n注：此游戏为实验性功能'
                self.gamestate = 0
                return True, tuple([True, text, "liferestart"])
            elif message == "1" and self.gamestart and self.gamestate == 0:
                batch = 3
                try:
                    res = ""
                    for i in range(batch):
                        x = self.run_life_ret.__next__()
                        res += f'\n{x[0]}{"——".join(x[1:])}'
                    # qq_platform.send(message_obj, res)
                    return True, tuple([True, res, "liferestart"])
                except StopIteration:
                    self.gamestate = 1
                    # qq_platform.send(message_obj,  f"\n\n【第{self.life.property.TMS}轮结束】你可以从本轮天赋中选择一项继承到下一轮：\n0 放弃继承")
                    # qq_platform.send(message_obj, '\n'.join([f"{i+1}.{t}" for i,t in enumerate(self.life.talent.talents)]))
                    # qq_platform.send(message_obj, "请输入希望继承的天赋序号：")
                    return True, tuple([True, f"\n\n【第{self.life.property.TMS}轮结束】你可以从本轮天赋中选择一项继承到下一轮：\n0 放弃继承\n" + '\n'.join([f"{i+1}.{t}" for i,t in enumerate(self.life.talent.talents)]) + "\n请输入希望继承的天赋序号：", "liferestart"])
                # for x in self.run_life_ret:
                #     res = f'\n{x[0]}{"——".join(x[1:])}'
                #     # print(f'\n{x[0]}{"——".join(x[1:])}',end='',flush=True
                #     qq_platform.send(message_obj, res)
                #     if(0 < i):
                #         i-=1
                #         continue
                #     if(msvcrt.getch() == b' '):
                #         i = 9
                
                # print()
                # print('\n'.join([f"{i+1}.{t}" for i,t in enumerate(self.life.talent.talents)]))
            elif self.gamestate == 1 and self.gamestart :
                # c = input("请输入希望继承的天赋序号（默认选择1）：")
                try:
                    c = int(message)
                except:
                    c = 1
                if c == 0:
                    qq_platform.send(message_obj, '没有继承任何天赋……')
                    # print('没有继承任何天赋……')
                    self.life.restart()
                inherit = 1
                try:
                    inherit = int(c)
                except:
                    pass
                qq_platform.send(message_obj, f'你的选择是：{inherit}')
                # print(f'你的选择是：{inherit}')
                self.life.restart(inherit)
                self.run_life_ret, text = self.run_life()
                self.gamestate = 0
                text += '\n输入1继续'
                return True, tuple([True, text, "liferestart"])
            elif message == "结束" or message == "exit" or message == "stop":
                self.gamestart = False
                self.gamestate = None
                self.session = []
                self.group_id = None
                self.life = None
                self.run_life_ret = None
                self.qq_platform = None
                return True, tuple([True, "结束游戏", "liferestart"])
            else:
                return False, None
        else:
            return False, None

        
    def run_life(self):
        self.life.setErrorHandler(self.on_error)
        self.life.setTalentHandler(self.pick_talent)
        self.life.setPropertyhandler(self.genp)

        self.life.choose()
        
        print(f'\n【第{self.life.property.TMS}轮开始】获得以下天赋：')
        t_str = ''
        for t in self.life.talent.talents:
            t_str += f'\n{t}'
        print(self.life.property)

        print("选择结束")

        ret = f'\n【第{self.life.property.TMS}轮开始】获得以下天赋：\n' + t_str + '\n' + str(self.life.property)

        return self.life.run(), ret
        
    def genp(self, prop):
        if(prop < 1):
            return { 'CHR': 0, 'INT': 0, 'STR': 0, 'MNY': 0 }
        ps = []
        for i in range(3):
            ps.append(id(i) % (int(prop * 2 / (4 - i)) + 1))
            if(10 < ps[-1]):
                ps[-1] = 10
            prop -= ps[-1]
        if(10 < prop):
            prop+=sum(ps)
            ps = [int(prop / 4)] * 3
            prop-=sum(ps)
        return {
            'CHR': ps[0],
            'INT': ps[1],
            'STR': ps[2],
            'MNY': prop
        }

    def on_error(self, e):
        raise e

    def pick_talent(self, ts):
        
        # print('\n【选择天赋】')
        # print('\n'.join([f'{i+1}.{t}' for i,t in enumerate(ts)]))
        ret = '\n【选择天赋】\n' + '\n'.join([f'{i+1}.{t}' for i,t in enumerate(ts)])
        self.qq_platform.send(self.group_id, ret)
        while True:
            # s = input('从中挑选一个你想拥有的天赋并输入序号（默认选择1）：')
            s = self.qq_platform.wait_for_message(self.group_id)
            if s == "结束" or s == "exit" or s == "stop":
                self.gamestart = False
                self.gamestate = None
                self.session = []
                self.group_id = None
                self.life = None
                self.run_life_ret = None
                self.qq_platform = None
                raise Exception("结束游戏")
            if s == '':
                return ts[0].id
            try:
                t = ts[int(s) - 1]
                print(f'你选择了：{t}')
                return t.id
            except HandlerException as e:
                print(e)
            except Exception as e:
                print('无法识别，请重新选择')
    
    def info(self):
        return {
            "name": "liferestart",
            "desc": "人生重开",
            "help": "人生重开",
            "version": "v1.0.0",
            "author": "cc004, Soulter"
        }