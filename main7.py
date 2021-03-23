import os
import psycopg2
import re
import pandas as pd
import codecs
import urllib
import datetime
from geopy.distance import geodesic
import requests
import json


from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,URITemplateAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,AudioMessage,
    ImageMessage, ImageSendMessage,ImagemapArea,ImagemapSendMessage, BaseSize,
    SeparatorComponent, QuickReply, QuickReplyButton, PostbackTemplateAction,DatetimePickerTemplateAction, MessageImagemapAction
)

#from datetime import datetime
from search import best_renkei, show_carousel, date_pick
#from test_smoking import search_area

     

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

app = Flask(__name__)


gobi = {
    "old" : "です",
    "young" : "だよ"
}

#DB情報
user = "cwlrjhcaaiuokb"
pwd = "d520472577f6d7ef56b2f5879978eb3067335b05c7c4ff430962bfceb703db32"
server = "ec2-54-225-116-36.compute-1.amazonaws.com"
port = "5432"
db = "d7oufjjv1lc0u3"


conn = psycopg2.connect("host=" + server + " port=" + port + " dbname=" + db + " user=" + user + " password=" + pwd)
#conn = psycopg2.connect(dbname = "sonogi-y")
conn.rollback()
#conn = MySQLdb.connect(user=REMOTE_DB_USER, passwd=REMOTE_DB_PASS, host=REMOTE_HOST, db=REMOTE_DB_NAME)
c = conn.cursor()
REMOTE_DB_TB = "user_info3"
REMOTE_DB_TB2 = "smoking"
REMOTE_DB_TB3 = "user_visit"
REMOTE_DB_TB4 = "basic_info"
#REMOTE_DB_TB3 = "soudan_info"
#REMOTE_DB_TB4 = "renkei"
#REMOTE_DB_TB5 = "postalcode"




@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


#######################################################



@handler.add(MessageEvent, message=TextMessage)
def on_messaging(event):
    text = event.message.text
    reply_token = event.reply_token
    user_id = event.source.user_id
    profiles = line_bot_api.get_profile(user_id=user_id)
    display_name = profiles.display_name

    if text == '電子タバコ' or text == '紙タバコ':
        line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text="位置情報を送ってください"),
                    TextSendMessage(text='line://nv/location'),
                ]
            )


#######################################################



@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    text = event.message.address
    lat = event.message.latitude
    lon = event.message.longitude
    user_id = event.source.user_id


    #smoking_areas = search_area(text)

    line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="近い順番に表示しています！"))

    sql = "select * from "+ REMOTE_DB_TB4+";"
    c.execute(sql)
    ret = c.fetchall()
    ret_df = pd.DataFrame(ret)

    dis_d = {}
    hr_d = {}
    dest_d = {}
    # (緯度, 経度)
    for n, h, lt, ln  in zip(ret_df[0], ret_df[1], ret_df[2], ret_df[3]):
        dest = (float(lt), float(ln))
        yourlocation = (lat, lon)
        destination = dest

        dis = geodesic(yourlocation, destination).km

        #print(dis)
        dis_d.update({n:dis})
        hr_d.update({n:h})
        dest_d.update({n:dest})

        # 267.9938255019848
    dis_d_sorted = sorted(dis_d.items(), key=lambda x:x[1])
    dis_d_top5 = dict(dis_d_sorted[0:5])
    dest_d_top5 = [dest_d[i] for i in dis_d_top5.keys()]



    carousel_columns = [
    CarouselColumn(
        text=value,
        title=key,
        actions=[
            #PostbackTemplateAction(
            URITemplateAction(
                label='ここにする',
                #data=key,
                uri=address
            ),
            PostbackTemplateAction(
                label='slackに通知する',
                data="slacking"
            )
        ]
    ) for key, value, address in (
        zip(
            #('喫煙所１', '喫煙所２', '喫煙所３', '喫煙所４', '喫煙所５'),
            #smoking_areas,
            #('喫煙所１の住所', '喫煙所2の住所', '喫煙所3の住所', '喫煙所4の住所', '喫煙所5の住所'),
            list(dis_d_top5.keys()),
            [hr_d[i] for i in list(dis_d_top5.keys())],
            ("https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[0][0])+","+str(dest_d_top5[0][1]),\
                "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[1][0])+","+str(dest_d_top5[1][1]),\
                "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[2][0])+","+str(dest_d_top5[2][1]),\
                "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[3][0])+","+str(dest_d_top5[3][1]),\
                "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[4][0])+","+str(dest_d_top5[4][1]),
            )
        )
    )
    ]
    message_template = CarouselTemplate(columns=carousel_columns)
    
    """


    payload = {
    "type": "carousel",
    "contents": [
        {
        "type": "bubble",
        "size": "micro",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "text",
                "text": "Brown Cafe",
                "weight": "bold",
                "size": "sm",
                "wrap": True
            },
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
                },
                {
                    "type": "text",
                    "text": "4.0",
                    "size": "xs",
                    "color": "#8c8c8c",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "baseline",
                    "spacing": "sm",
                    "contents": [
                    {
                        "type": "text",
                        "text": "東京旅行",
                        "wrap": True,
                        "color": "#8c8c8c",
                        "size": "xs",
                        "flex": 5
                    }
                    ]
                }
                ]
            }
            ],
            "spacing": "sm",
            "paddingAll": "13px"
        }
        },
        {
        "type": "bubble",
        "size": "micro",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "text",
                "text": "Brow&Cony's Restaurant",
                "weight": "bold",
                "size": "sm",
                "wrap": True
            },
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
                },
                {
                    "type": "text",
                    "text": "4.0",
                    "size": "sm",
                    "color": "#8c8c8c",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "baseline",
                    "spacing": "sm",
                    "contents": [
                    {
                        "type": "text",
                        "text": "東京旅行",
                        "wrap": True,
                        "color": "#8c8c8c",
                        "size": "xs",
                        "flex": 5
                    }
                    ]
                }
                ]
            }
            ],
            "spacing": "sm",
            "paddingAll": "13px"
        }
        },
        {
        "type": "bubble",
        "size": "micro",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "text",
                "text": "Tata",
                "weight": "bold",
                "size": "sm"
            },
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                },
                {
                    "type": "icon",
                    "size": "xs",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
                },
                {
                    "type": "text",
                    "text": "4.0",
                    "size": "sm",
                    "color": "#8c8c8c",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "baseline",
                    "spacing": "sm",
                    "contents": [
                    {
                        "type": "text",
                        "text": "東京旅行",
                        "wrap": True,
                        "color": "#8c8c8c",
                        "size": "xs",
                        "flex": 5
                    }
                    ]
                }
                ]
            }
            ],
            "spacing": "sm",
            "paddingAll": "13px"
        }
        }
    ]
    }
    """

    line_bot_api.push_message(
        to=user_id,
        messages=TemplateSendMessage(alt_text='carousel template', template=message_template)
    )
    #container_obj = FlexSendMessage.new_from_json_dict(payload)
    #line_bot_api.push_message(user_id, messages=container_obj)



#######################################################




@handler.add(PostbackEvent)
def handle_postback(event):
    """
    ポストバックに対応したメソッド。
    性別の登録。
    質問の投稿。
    回答の投稿。
    """
    user_id = event.source.user_id
    profiles = line_bot_api.get_profile(user_id=user_id)
    display_name = profiles.display_name
        



"""
    elif event.postback.data == '喫煙所１' or event.postback.data == '喫煙所２' or event.postback.data == '喫煙所３'\
            or event.postback.data == '喫煙所４' or event.postback.data == '喫煙所５':
    #elif event.postback.label == "ここにする":
        choice = event.postback.data

        sql = "select MAX(date) from "+REMOTE_DB_TB3+ " WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        ret = c.fetchall()
        latest = str(ret[0][0])

        preference1 = event.postback.data
        sql="update "+REMOTE_DB_TB3+ " set choice = '"+choice+"' WHERE user_id = '"+str(user_id)+"' and date = '"+latest+"';"
        c.execute(sql)
        conn.commit()
"""


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)