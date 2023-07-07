# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import random
import requests
import datetime
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class GetStandings(Action):
    def name(self) -> Text:
        return "action_standings"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        url = "https://esports-api.lolesports.com/persisted/gw/getStandingsV3?hl=ko-KR&tournamentId=110371551277508787"
        headers = {
            "X-API-Key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
        }

        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            standings = response.json()["data"]["standings"][0]["stages"][0]["sections"][0]["rankings"]
            team_standings = []
            for ordinal in standings:
                teams = ordinal.get("teams", [])
                for team in teams:
                    team_name = team["name"]
                    team_rank = ordinal["ordinal"]
                    team_standings.append(f"{team_rank}: {team_name}")

            standings_str = "\n".join(team_standings)
            dispatcher.utter_message("2023 Summer LCK 순위는 다음과 같습니다.")
            dispatcher.utter_message(standings_str)
        except requests.exceptions.RequestException as e:
            error_message = "API 요청 중 오류가 발생했습니다. 나중에 다시 시도해주세요."
            dispatcher.utter_message(error_message)
            dispatcher.utter_message(str(e))

        return []

class GetSchedule(Action):
    def name(self) -> Text:
        return "action_schedule"

    def filter_schedule_by_selected_date(self, events, selected_date):
        filtered_events = []
        for event in events:
            start_time = datetime.datetime.strptime(event['startTime'], '%Y-%m-%dT%H:%M:%S%z')
            if start_time.year == selected_date.year and start_time.month == selected_date.month and start_time.day == selected_date.day:
                filtered_events.append(event)
        return filtered_events
    
    def format_start_time(self, start_time):
        parsed_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S%z')
        formatted_time = parsed_time.strftime("%m월 %d일 %H시 %M분")
        return formatted_time

    def combine_api_responses(self, api_responses):
        combined_events = []
        for response in api_responses:
            events = response.json()['data']['schedule']['events']
            combined_events.extend(events)
        return combined_events

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_month = next(tracker.get_latest_entity_values("Month"), None)
        user_day = next(tracker.get_latest_entity_values("Day"), None)

        if user_month:
            user_month = user_month.replace("월", "")

        if user_day:
            user_day = user_day.replace("일", "")

        if user_month and user_day:
            current_year = datetime.datetime.now().year
            selected_date = datetime.datetime.strptime(f"{current_year}-{user_month}-{user_day}", "%Y-%m-%d")
        else:
            dispatcher.utter_message("에러가 발생하였습니다. 0월 0일 형식으로 입력해주세요.")
            return []

        urls = [
            "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=ko-KR&leagueId=98767991310872058",
            "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=ko-KR&leagueId=98767991310872058&pageToken=b2xkZXI6OjExMDM3MTU1MTI3OTAxNjI0MA==",
            "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=ko-KR&leagueId=98767991310872058&pageToken=bmV3ZXI6OjExMDM3MTU1MTI3OTA4MTg3Ng=="
        ]

        headers = {
            "X-API-Key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
        }

        api_responses = []
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=5)  # Set timeout to 5 seconds
                response.raise_for_status()  # Raise an exception if the response status is not 200
                api_responses.append(response)
            except requests.exceptions.RequestException:
                dispatcher.utter_message("죄송합니다. 일정을 가져오는 중 오류가 발생한 것 같습니다.")
                return []

        events = self.combine_api_responses(api_responses)
        filtered_events = self.filter_schedule_by_selected_date(events, selected_date)

        if not filtered_events:
            dispatcher.utter_message("죄송합니다. 선택하신 날짜에는 경기가 없습니다.")
            return []

        team_info = []
        for event in filtered_events:
            teams = event['match']['teams']
            team1_name = teams[0]['name']
            team2_name = teams[1]['name']
            team1_wins = teams[0]['result']['gameWins']
            team2_wins = teams[1]['result']['gameWins']
            start_time = self.format_start_time(event['startTime'])
            state = event['state']

            if state == "completed":
                team_info.append(f"{team1_name} 대 {team2_name}의 경기 결과는 {team1_wins} 대 {team2_wins}로 ")
                if team1_wins > team2_wins:
                    team_info.append(f"{team1_name}이 승리하였습니다.\n")
                else:
                    team_info.append(f"{team2_name}이 승리하였습니다.\n")
            else:
                team_info.append(f"{team1_name} 과 {team2_name}의 경기가 {start_time}에 예정되어 있습니다.\n")

        dispatcher.utter_message(user_month + "월 " + user_day + "일 경기는 다음과 같습니다.")
        dispatcher.utter_message("".join(team_info))

        return []
    
class GetTeamInfo(Action):
    def name(self) -> Text:
        return "action_teaminfo"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        team_name = next(tracker.get_latest_entity_values("team_name"), None)

        if team_name == "T1" or team_name == "티원":
            messages = [
                "T1은 리그 오브 레전드에서 한국을 대표하는 프로게임단으로, 기존에는 SK텔레콤 T1으로 알려져 있었습니다. T1은 전 세계적으로 가장 성공적인 리그 오브 레전드 팀 중 하나로 알려져 있으며, 많은 팬들에게 사랑받고 있습니다.",
                "T1은 많은 리그 오브 레전드 전문가와 팬들 사이에서 전설적인 선수들과 함께해온 팀입니다. 그들은 다양한 리그와 국제 대회에서 우승을 차지하였으며, 특히 리그 오브 레전드 월드 챔피언십에서 많은 성과를 거두었습니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        elif team_name == "GEN" or team_name == "젠지":
            messages = [
                "젠지(Gen.G)는 한국의 전문 리그 오브 레전드(LoL) 팀으로 잘 알려진 팀입니다. 이 팀은 이전에는 Samsung Galaxy로 알려져 있었습니다. 젠지는 2012년에 설립되었으며, 2013년부터 리그 오브 레전드 경기에 참가하였습니다.",
                "젠지는 리그 오브 레전드 경기에서 성과를 거두며 많은 팬들에게 인기를 얻었습니다. 특히, 2014년과 2017년에는 월드 챔피언십에서 각각 1위를 차지하였습니다. 이를테면, 2014년 월드 챔피언십에서는 그들이 Samsung White라는 이름으로 참가하여 결승에서 Star Horn Royal Club를 이기고 우승을 차지했습니다."
                "젠지는 팀의 이름을 Gen.G로 변경한 후에도 리그 오브 레전드 경기에서 성공적인 결과를 이뤄내고 있습니다. 리그 오브 레전드 경기뿐만 아니라 다른 게임들에서도 다양한 분야에서 활동하고 있으며, 전문성과 성과를 바탕으로 국제적으로도 알려진 팀 중 하나입니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        elif team_name == "DRX" or team_name == "디알엑스":
            messages = [
                "DRX는 한국의 전문 리그 오브 레전드(LoL) 팀입니다. 이전에는 KINGZONE DragonX 및 ROX Tigers로도 알려져 있었습니다. DRX는 한국 e스포츠 조직인 DRX의 리그 오브 레전드 팀으로 활동하고 있습니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        elif team_name == "KT" or team_name == "케이티":
            messages = [
                "KT는 한국의 전문 리그 오브 레전드(LoL) 팀인 KT Rolster를 가리킵니다. KT는 한국 통신사인 KT(한국통신)의 스폰서를 받고 있는 팀으로, 리그 오브 레전드 경기에 참가하며 활동하고 있습니다.",
                "KT Rolster는 경쟁력 있는 선수들로 구성된 팀으로 알려져 있습니다. 많은 팬들에게 인기를 얻고 있으며, 한때는 한국 e스포츠의 가장 강력한 팀 중 하나로 꼽히기도 했습니다. KT Rolster는 리그 오브 레전드 경기에서 경쟁력을 유지하며, 국내 및 국제 대회에서 좋은 성과를 내기 위해 노력하고 있습니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)
            
        elif team_name == "HLE" or team_name == "한화" or team_name == "한화생명":
            messages = [
                "한화생명 eSports (Hanwha Life Esports)는 한국의 전문 리그 오브 레전드(LoL) 팀입니다. 한화생명은 한국의 보험 및 금융 서비스 기업인 한화생명이 스폰서로 지원하고 있는 팀입니다.",
                "한화생명 eSports는 2018년에 설립되었으며, 한화생명의 eSports 진출을 위한 첫 번째 프로게임단으로 출범하였습니다. 팀은 리그 오브 레전드 경기에 참가하여 활동하고 있으며, 한국 리그인 LCK에서 경쟁하고 있습니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        elif team_name == "DK" or team_name == "디플" or team_name == "디플러스 기아":
            messages = [
                "담원 기아(DAMWON KIA)은 한국의 전문 리그 오브 레전드(LoL) 팀으로 알려져 있습니다. 이 팀은 2017년에 설립되었으며, 한국 e스포츠 조직인 Kia Tigers의 자회사로 시작되었습니다. 이후에는 독립적인 팀으로서 활동하고 있습니다.",
                "담원 게이밍은 리그 오브 레전드 경기에서 많은 성과를 거두며 전 세계적으로 인정받고 있는 팀입니다. 특히 2020년에는 LCK 스플릿에서 우승을 차지하였으며, 이후에는 월드 챔피언십에서도 최종 우승을 차지하며 세계적인 주목을 받았습니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        elif team_name == "LSB" or team_name == "리브" or team_name == "샌드박스" or team_name == "리브 샌드박스":
            messages = [
                "리브 샌드박스(Liv Sandbox)는 한국의 전문 리그 오브 레전드(LoL) 팀입니다. 이 팀은 2019년에 설립되었으며, 한국 e스포츠 조직인 Team Dynamics의 후속 팀으로 시작되었습니다.",
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        elif team_name == "KDF" or team_name == "광동" or team_name == "광동 프릭스":
            messages = [
                "광동 프릭스는 2015년에 설립되었으며, 리그 오브 레전드 경기에 참가하여 경쟁하고 있습니다. 팀은 다양한 시즌과 대회에서 활약하며, 꾸준한 성과를 거두고 있습니다.",
                "광동 프릭스는 경기에서 다양한 전략과 선수들의 뛰어난 플레이로 인해 주목을 받고 있습니다. 특히, 한때는 Longzhu Gaming이라는 이름으로 활동하며 2017년에 LCK 스플릿에서 우승을 차지하기도 했습니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        elif team_name == "BRO" or team_name == "브리온" or team_name == "프레딧" or team_name == "프레딧 브리온":
            messages = [
                "프레딧 브리온은 2020년에 설립되었으며, 리그 오브 레전드 경기에 참가하여 경쟁하고 있습니다. 이전에는 Team Dynamics라는 이름으로 활동하였으며, 2021년에 프레딧의 후원을 받아 팀명을 변경하였습니다.",
                "프레딧 브리온은 리그 오브 레전드 경기에서 경쟁력을 유지하며 팬들에게 많은 관심과 사랑을 받고 있습니다. 한국 eSports 씬에서 성장하고 발전하는 모습을 보여주며, 앞으로 더 좋은 성과를 이루기 위해 노력할 것으로 기대됩니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        elif team_name == "NS" or team_name == "농심" or team_name == "농심 레드포스":
            messages = [
                "농심 레드포스 (Nongshim RedForce)는 한국의 전문 리그 오브 레전드(LoL) 팀입니다. 이 팀은 한국의 대표적인 식품 기업인 농심의 후원을 받고 활동하고 있습니다.",
                "농심 레드포스는 경기에서 뛰어난 전략과 플레이를 통해 주목을 받고 있습니다. 특히, 2021년에는 LCK 스플릿에서 톱 5에 진출하여 좋은 성과를 거두었습니다."
            ]
            selected_message = random.choice(messages)
            dispatcher.utter_message(selected_message)

        else :
            dispatcher.utter_message("정확한 팀명을 입력해주시기 바랍니다.")

class GetTeamPlayers(Action):
    def name(self) -> Text:
        return "action_teamplayers"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        team_name = next(tracker.get_latest_entity_values("team_name"), None)

        if team_name == "T1" or team_name == "티원":
            dispatcher.utter_message("T1의 선수는 다음과 같습니다.\n- Top: Zeus\n- Jug: Oner\n- Mid: Faker\n- Adc: Gumayusi\n- Sup: Keria")
        elif team_name == "GEN" or team_name == "젠지":
            dispatcher.utter_message("GEN의 선수는 다음과 같습니다.\n- Top: Doran\n- Jug: Peanut\n- Mid: Chovy\n- Adc: Peyz\n- Sup: Delight")
        elif team_name == "DRX" or team_name == "디알엑스":
            dispatcher.utter_message("DRX의 선수는 다음과 같습니다.\n- Top: Rascal\n- Jug: Croco\n- Mid: Kyeahoo\n- Adc: Paduck\n- Sup: BeryL")
        elif team_name == "KT" or team_name == "케이티":
            dispatcher.utter_message("KT의 선수는 다음과 같습니다.\n- Top: Kiin\n- Jug: Cuzz\n- Mid: Bdd\n- Adc: Aiming\n- Sup: Lehends")
        elif team_name == "HLE" or team_name == "한화" or team_name == "한화생명":
            dispatcher.utter_message("HLE의 선수는 다음과 같습니다.\n- Top: Kingen\n- Jug: Clid\n- Mid: ZEKA\n- Adc: Viper\n- Sup: Life")
        elif team_name == "DK" or team_name == "디플" or team_name == "디플러스 기아":
            dispatcher.utter_message("DK의 선수는 다음과 같습니다.\n- Top: Canna\n- Jug: Canyon\n- Mid: Showmaker\n- Adc: Deft\n- Sup: Kellin")
        elif team_name == "LSB" or team_name == "리브" or team_name == "샌드박스" or team_name == "리브 샌드박스":
            dispatcher.utter_message("LSB의 선수는 다음과 같습니다.\n- Top: Burdol\n- Jug: Willer\n- Mid: Clozer\n- Adc: Teddy\n- Sup: Kael")
        elif team_name == "KDF" or team_name == "광동" or team_name == "광동 프릭스":
            dispatcher.utter_message("KDF의 선수는 다음과 같습니다.\n- Top: DuDu\n- Jug: YoungJae\n- Mid: BuLLDoG\n- Adc: Taeyoon\n- Sup: Jun")
        elif team_name == "BRO" or team_name == "브리온" or team_name == "프레딧" or team_name == "프레딧 브리온":
            dispatcher.utter_message("BRO의 선수는 다음과 같습니다.\n- Top: Morgan\n- Jug: Umti\n- Mid: Karis\n- Adc: Hena\n- Sup: Effort")
        elif team_name == "NS" or team_name == "농심" or team_name == "농심 레드포스":
            dispatcher.utter_message("BRO의 선수는 다음과 같습니다.\n- Top: DnDn\n- Jug: Sylvie\n- Mid: Quad\n- Adc: Vital\n- Sup: Peter")
        else :
            dispatcher.utter_message("정확한 팀명을 입력해주시기 바랍니다.")