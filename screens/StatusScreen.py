import asyncio

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation

from common.now import now
from common.visibility import show,hide

class ParticipantUI(BoxLayout):

    def __init__(self,nickname):
        super().__init__()
        self.ids["nickname"].text = nickname

    def declareWin(self):
        win = self.ids["win"]
        win.text = "WIN"
        show(win,animation=True)

    def declareGameOver(self):
        self.ids["win"].text = "GAME OVER"
    
    def changeInfoText(self,text):
        self.ids["info"].text = text

class StatusScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp  
        self.app = App.get_running_app()

    def on_pre_enter(self):
        participantUIs = self.ids["participantUIs"]
        participantUIs.clear_widgets()
        hide(self.ids["calculationLabel"])

        self.statusTask = asyncio.create_task(self.__status())
    
    async def __status(self):
        try:
            titleLabel = self.ids["titleLabel"]
            calculationLabel = self.ids["calculationLabel"]
            infoLabel = self.ids["infoLabel"]
            participantUIs = self.ids["participantUIs"]

            print("In status")

            gameInfo = self.app.globalGameInfo

            ps = gameInfo["participants"]

            pus = list(map(lambda p: {**p, "ui": ParticipantUI(p["nickname"])},ps))

            guessSum = 0
            for i in range(len(pus)):
                pu = pus[i]
                guess = pu["guess"]

                # Calculate sum
                guessSum += guess

                # Gradually prepare for the calculationLabel
                pu["ui"].changeInfoText(str(guess))
                if i == 0:
                    calculationLabel.text = "(" + str(guess)
                else:
                    calculationLabel.text = calculationLabel.text + " + "  + str(guess)
                participantUIs.add_widget(pu["ui"])

            # finish preparing calculationLabel
            average = round(guessSum/len(pus),2)
            target = round(gameInfo["target"],2)
            calculationLabel.text = calculationLabel.text + f')/{len(pus)} = {average}\n{average} * 0.8 = {target}'
        
            await asyncio.sleep(1)

            # Show calculationLabel
            show(calculationLabel,animation=True)

            await asyncio.sleep(1)

            for i in range(len(pus)):
                pu = pus[i]
                if pu["id"] in gameInfo["winners"]:
                    pu["ui"].declareWin()


            await asyncio.sleep(2)
            
            if gameInfo["roundStartTime"]-now() > 0:
                print("Waiting for round start")
                await asyncio.sleep((gameInfo["roundStartTime"]-now())/1000)

            self.app.globalGameInfo = gameInfo
            self.manager.current = "game"

        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __status",str(e))