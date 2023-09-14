import asyncio

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from common.now import now
from common.visibility import show, hide

class JoinRoomParticipantUI(BoxLayout):
    def __init__(self):
        super().__init__()

    def showPfp(self):
        show(self)

    def hidePfp(self):
        hide(self)

    def showNickname(self,nickname):
        if len(nickname) > 10:
            self.ids["nickname"].font_size = "12sp"
        else:
            self.ids["nickname"].font_size = "14sp"
        self.ids["nickname"].text = nickname
    

class JoinRoomScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp 
        self.app = App.get_running_app()

    def on_pre_enter(self):
        self.gameStarted = False
        joinRoomParticipantUIs = self.ids["joinRoomParticipantUIs"]
        joinRoomParticipantUIs.clear_widgets()

        titleLabel = self.ids["titleLabel"]
        bodyLabel = self.ids["bodyLabel"]
        titleLabel.text = "Connecting to server"
        bodyLabel.text = "Please wait..."

        self.ids["exitButton"].background_color = [1,0,0,1]
        self.joinRoomTask = asyncio.create_task(self.__joinRoom())
    
    async def __joinRoom(self):
        try:
            titleLabel = self.ids["titleLabel"]
            bodyLabel = self.ids["bodyLabel"]
            joinRoomParticipantUIs = self.ids["joinRoomParticipantUIs"]
            pus = [] # list of joinRoomParticipantUIs

            print("In join room")

            event = await self.qApp.get()

            if event["event"] == "serverConnected":
                participantCount = event["participantsCount"]
                participantsPerGame = event["participantsPerGame"]
                titleLabel.text = f'Waiting for participants to join ({participantCount}/{participantsPerGame})'
                # Create that many participants
                for i in range(participantsPerGame):
                    pu = JoinRoomParticipantUI()
                    pus.append(pu)
                    joinRoomParticipantUIs.add_widget(pu)
                for i in range(participantCount):
                    pus[i].showPfp()
                for i in range(participantCount,participantsPerGame):
                    pus[i].hidePfp()
            else:
                assert(event["event"] == "serverConnectionFailed",'condition event["event"] == "serverConnectionFailed" not met')
                titleLabel.text = "An error occured"
                bodyLabel.text = event["errorMsg"]
                return
            
            event = await self.qApp.get()

            while event["event"] != "gameStart":
                assert(event["event"]=="updateParticipantsCount",'condition event["event"]=="updateParticipantsCount" not met')
                participantCount = event["participantsCount"]
                participantsPerGame = event["participantsPerGame"]
                titleLabel.text = f'Waiting for participants to join ({participantCount}/{participantsPerGame})'
                for i in range(participantCount):
                    pus[i].showPfp()
                for i in range(participantCount,participantsPerGame):
                    pus[i].hidePfp()
                event = await self.qApp.get()

            assert(event["event"]=="gameStart",'condition event["event"]=="gameStart" not met')
            print("gameStart event received by app")
            self.gameStarted = True
            gameInfo = event
            titleLabel.text = f'Game is starting ({participantCount}/{participantsPerGame})'
            bodyLabel.text = "The game will start shortly"
            # print(self.ids["exitButton"].background_color)
            self.ids["exitButton"].background_color = [0.5,0.5,0.5, 1]
            # print(self.ids["exitButton"].background_color)
            for i in range(len(gameInfo["participants"])):
                p = gameInfo["participants"][i]
                pus[i].showNickname(p["nickname"])

            if gameInfo["roundStartTime"]-now() > 0:
                print("Waiting for round start")
                await asyncio.sleep((gameInfo["roundStartTime"]-now())/1000)

            self.app.globalGameInfo = gameInfo
            self.manager.current = "game"

        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __joinRoom",repr(e))
    
    def exitGame(self):
        if(self.gameStarted):
            print("Game started cannot exit")
        else:
            print("quit game")
            self.qGame.put_nowait({
                "event": "quitGame"
            })
            self.manager.current = "home"
            return
        