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
from model.platform.qqchan import QQChan
from cores.qqbot.global_object import AstrMessageEvent
from typing import Union

class GameSession:
    def __init__(self, session_id: int, platform_obj) -> None:
        self.gamestart = False
        self.gamestate = None
        self.life: Life = None
        self.platform_obj: Union[QQ, QQChan] = platform_obj
        self.session_id = session_id
        self.run_life_ret = None
        self.latest_message_obj = None

    def __str__(self) -> str:
        return str(self.__dict__)


class liferestartPlugin:
    def __init__(self) -> None:
        print("Remake :)")
        # 本脚本绝对路径
        self.path = os.path.dirname(os.path.abspath(__file__))
        Life.load(self.path + '/data')
        self.session = {}
        self.commands = ["重开", "1", "结束", "stop", "exit"]

    def run(self, ame: AstrMessageEvent):
        message = ame.message_str
        if message not in self.commands:
            return False, None

        message_obj = ame.message_obj
        if message_obj.type != "GuildMessage":
            platform = ame.gocq_platform
        else:
            platform = ame.qq_sdk_platform
        session_id = ame.session_id
        if ame.session_id not in self.session:
            game_session = GameSession(session_id, platform)
            self.session[session_id] = game_session
        else:
            game_session = self.session[session_id]
        game_session.latest_message_obj = message_obj
        print(message)
        print(game_session)
        
        if message == "重开":
            game_session.life = Life()
            run_life_ret, text = self.run_life(game_session)
            game_session.run_life_ret = run_life_ret
            game_session.gamestart = True
            text += '\n输入 1 继续。输入结束 stop exit 来结束游戏.\n\n注：此游戏为实验性功能'
            game_session.gamestate = 0
            return True, tuple([True, text, "liferestart"])
        elif message == "1" and game_session.gamestart and game_session.gamestate == 0:
            batch = 3
            try:
                res = ""
                for i in range(batch):
                    x = game_session.run_life_ret.__next__()
                    res += f'\n{x[0]}{"——".join(x[1:])}'
                # qq_platform.send(message_obj, res)
                return True, tuple([True, res, "liferestart"])
            except StopIteration:
                game_session.gamestate = 1
                return True, tuple([True, f"\n\n【第{game_session.life.property.TMS}轮结束】你可以从本轮天赋中选择一项继承到下一轮：\n0 放弃继承\n" + '\n'.join([f"{i+1}.{t}" for i,t in enumerate(self.life.talent.talents)]) + "\n请输入希望继承的天赋序号：", "liferestart"])
        elif game_session.gamestate == 1 and game_session.gamestart :
            # c = input("请输入希望继承的天赋序号（默认选择1）：")
            try:
                c = int(message)
            except:
                c = 1
            if c == 0:
                game_session.platform_obj.send(message_obj, '没有继承任何天赋……')
                # print('没有继承任何天赋……')
                game_session.life.restart()
            inherit = 1
            try:
                inherit = int(c)
            except:
                pass
            game_session.platform_obj.send(message_obj, f'你的选择是：{inherit}')
            # print(f'你的选择是：{inherit}')
            game_session.life.restart(inherit)
            game_session.run_life_ret, text = self.run_life(game_session)
            game_session.gamestate = 0
            text += '\n输入1继续'
            return True, tuple([True, text, "liferestart"])
        elif message == "结束" or message == "exit" or message == "stop":
            game_session.gamestart = False
            game_session.gamestate = None
            game_session.session_id = None
            game_session.life = None
            game_session.run_life_ret = None
            game_session.platform_obj = None
            return True, tuple([True, "结束游戏", "liferestart"])
        else:
            return False, None

        
    def run_life(self, game_session: GameSession):
        game_session.life.setErrorHandler(self.on_error)
        game_session.life.setTalentHandler(self.pick_talent, game_session)
        game_session.life.setPropertyhandler(self.genp)

        game_session.life.choose()
        
        print(f'\n【第{game_session.life.property.TMS}轮开始】获得以下天赋：')
        t_str = ''
        for t in game_session.life.talent.talents:
            t_str += f'\n{t}'
        print(game_session.life.property)

        print("选择结束")

        ret = f'\n【第{game_session.life.property.TMS}轮开始】获得以下天赋：\n' + t_str + '\n' + str(game_session.life.property)

        return game_session.life.run(), ret
        
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

    def pick_talent(self, ts, game_session: GameSession):
        
        # print('\n【选择天赋】')
        # print('\n'.join([f'{i+1}.{t}' for i,t in enumerate(ts)]))
        ret = '\n【选择天赋】\n' + '\n'.join([f'{i+1}.{t}' for i,t in enumerate(ts)])
        game_session.platform_obj.send(game_session.latest_message_obj, ret)
        while True:
            # s = input('从中挑选一个你想拥有的天赋并输入序号（默认选择1）：')
            message = game_session.platform_obj.wait_for_message(game_session.session_id)
            game_session.latest_message_obj = message
            s = ''
            for i in message.message:
                if isinstance(i, Plain):
                    s += str(i.text).strip()
                
            if s == "结束" or s == "exit" or s == "stop":
                game_session.gamestart = False
                game_session.gamestate = None
                game_session.session_id = None
                game_session.life = None
                game_session.run_life_ret = None
                game_session.platform_obj = None
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
            "desc": "人生重开模拟器。输入`重开`启动游戏。",
            "help": "人生重开",
            "version": "v1.1.0",
            "author": "cc004, Soulter"
        }
