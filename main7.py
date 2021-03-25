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
#REMOTE_DB_TB = "user_info3"
#REMOTE_DB_TB2 = "smoking"
REMOTE_DB_TB3 = "user_preference"
REMOTE_DB_TB4 = "smokingarea_info2"
#REMOTE_DB_TB3 = "soudan_info"
#REMOTE_DB_TB4 = "renkei"
#REMOTE_DB_TB5 = "postalcode"

dis_d = {}
hr_d = {}
dest_d = {}
paper_d = {}
electro_d = {}
style_d = {}

location_ltln = []


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
        sql = "insert into "+REMOTE_DB_TB3+ " values ('"+str(user_id)+"',current_timestamp,'"+text+"');"
        c.execute(sql)
        conn.commit()

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

    location_ltln.append(lat)
    location_ltln.append(lon)

    #今日の気分を確かめる
    sql = "select MAX(date) from "+REMOTE_DB_TB3+ " WHERE user_id = '"+str(user_id)+"';"
    c.execute(sql)
    ret = c.fetchall()
    latest = str(ret[0][0])
    sql = "select preference from "+ REMOTE_DB_TB3+" WHERE date ='"+latest+"';" 
    c.execute(sql)
    ret = c.fetchall()
    pref = str(ret[0][0])
    
    #今日の気分に該当する喫煙所だけの距離を計
    line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="近い順番に表示しています！"))

    if pref == "電子タバコ":
        sql = "select * from "+ REMOTE_DB_TB4+" where electronic ='あり';"
    elif pref == "紙タバコ":
        sql = "select * from "+ REMOTE_DB_TB4+" where paper ='あり';"

    c.execute(sql)
    ret = c.fetchall()
    ret_df = pd.DataFrame(ret)

    #dis_d = {}
    #hr_d = {}
    #dest_d = {}
    #paper_d = {}
    #electro_d = {}
    #style_d = {}
    # (緯度, 経度)
    for n, h, lt, ln, st, pp, el  in zip(ret_df[0], ret_df[1], ret_df[2], ret_df[3], ret_df[4], ret_df[5], ret_df[6]):
        dest = (float(lt), float(ln))
        yourlocation = (lat, lon)
        destination = dest

        dis = geodesic(yourlocation, destination).km

        #print(dis)
        dis_d.update({n:dis})
        hr_d.update({n:h})
        dest_d.update({n:dest})
        paper_d.update({n:pp})
        electro_d.update({n:el})
        style_d.update({n:st})

        # 267.9938255019848
    dis_d_sorted = sorted(dis_d.items(), key=lambda x:x[1])
    dis_d_top5 = dict(dis_d_sorted[0:3])
    dest_d_top5 = [dest_d[i] for i in dis_d_top5.keys()]
    hr_d_top5 = [hr_d[i] for i in list(dis_d_top5.keys())]
    paper_d_top5 = [paper_d[i] for i in dis_d_top5.keys()]
    electro_d_top5 = [electro_d[i] for i in dis_d_top5.keys()]
    style_d_top5 = [style_d[i] for i in dis_d_top5.keys()]


    link1 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[0][0])+","+str(dest_d_top5[0][1])+"&openExternalBrowser=1"
    link2 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[1][0])+","+str(dest_d_top5[1][1])+"&openExternalBrowser=1"
    link3 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[2][0])+","+str(dest_d_top5[2][1])+"&openExternalBrowser=1"
    

    messages = {
    "type": "carousel",
    "contents": [
        {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "text",
                "text": list(dis_d_top5.keys())[0],
                "wrap": True,
                "weight": "bold",
                "size": "xl"
            },
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "text",
                    "text": hr_d_top5[0],
                    "wrap": True,
                    "weight": "bold",
                    "size": "md",
                    "flex": 0
                }
                ]
            },
            {
                "type": "text",
                "text": "紙巻き"+paper_d_top5[0]+" 加熱式"+electro_d_top5[0],
                "wrap": True,
                "size": "md",
                "margin": "md",
                "flex": 0
            },
            {
                "type": "text",
                "text": style_d_top5[0],
                "wrap": True,
                "size": "md",
                "margin": "md",
                "flex": 0
            }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "button",
                "style": "primary",
                "action": {
                "type": "uri",
                "label": "マップを開く",
                "uri": link1
                }
            }
            ]
        }
        },
        {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "text",
                "text": list(dis_d_top5.keys())[1],
                "wrap": True,
                "weight": "bold",
                "size": "xl"
            },
            {
                "type": "box",
                "layout": "baseline",
                "flex": 1,
                "contents": [
                {
                    "type": "text",
                    "text": hr_d_top5[1],
                    "wrap": True,
                    "weight": "bold",
                    "size": "md",
                    "flex": 0
                }
                ]
            },
            {
                "type": "text",
                "text": "紙巻き"+paper_d_top5[1]+" 加熱式"+electro_d_top5[1],
                "wrap": True,
                "size": "md",
                "margin": "md",
                "flex": 0
            },
            {
                "type": "text",
                "text": style_d_top5[1],
                "wrap": True,
                "size": "md",
                "margin": "md",
                "flex": 0
            }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "button",
                "flex": 2,
                "style": "primary",
                "action": {
                "type": "uri",
                "label": "マップを開く",
                "uri": link2
                }
            }
            ]
        }
        },
        {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "text",
                "text": list(dis_d_top5.keys())[2],
                "wrap": True,
                "weight": "bold",
                "size": "xl"
            },
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "text",
                    "text": hr_d_top5[2],
                    "wrap": True,
                    "weight": "bold",
                    "size": "md",
                    "flex": 0
                }
                ]
            },
            {
                "type": "text",
                "text": "紙巻き"+paper_d_top5[2]+" 加熱式"+electro_d_top5[2],
                "wrap": True,
                "size": "md",
                "margin": "md",
                "flex": 0
            },
            {
                "type": "text",
                "text": style_d_top5[2],
                "wrap": True,
                "size": "md",
                "margin": "md",
                "flex": 0
            }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "button",
                "style": "primary",
                "action": {
                "type": "uri",
                "label": "マップを開く",
                "uri": link3
                }
            }
            ]
        }
        },
        {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "button",
                "flex": 1,
                "gravity": "center",
                "action": {
                "type": "postback",
                "label": "次の３件を見る",
                "data": "4-6"
                }
            }
            ]
        }
        }
    ]
    }

    #f = open('./template.json', 'r')
    #messages = json.load(f)
    messages = FlexSendMessage(alt_text="options", contents=messages)
    #メッセージ送信
    line_bot_api.push_message(user_id, messages=messages)

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

    if event.postback.data == "4-6":
        dis_d_sorted = sorted(dis_d.items(), key=lambda x:x[1])
        dis_d_top5 = dict(dis_d_sorted[3:6])
        dest_d_top5 = [dest_d[i] for i in dis_d_top5.keys()]
        hr_d_top5 = [hr_d[i] for i in list(dis_d_top5.keys())]
        paper_d_top5 = [paper_d[i] for i in dis_d_top5.keys()]
        electro_d_top5 = [electro_d[i] for i in dis_d_top5.keys()]
        style_d_top5 = [style_d[i] for i in dis_d_top5.keys()]

        lat = location_ltln[0]
        lon = location_ltln[1]
        link4 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[0][0])+","+str(dest_d_top5[0][1])+"&openExternalBrowser=1"
        link5 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[1][0])+","+str(dest_d_top5[1][1])+"&openExternalBrowser=1"
        link6 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[2][0])+","+str(dest_d_top5[2][1])+"&openExternalBrowser=1"
        
        messages = {
        "type": "carousel",
        "contents": [
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[0],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[0],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[0]+" 加熱式"+electro_d_top5[0],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[0],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link4
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[1],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "flex": 1,
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[1],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[1]+" 加熱式"+electro_d_top5[1],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[1],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "flex": 2,
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link5
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[2],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[2],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[2]+" 加熱式"+electro_d_top5[2],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[2],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link6
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "flex": 1,
                    "gravity": "center",
                    "action": {
                    "type": "postback",
                    "label": "次の３件を見る",
                    "data": "7-9"
                    }
                }
                ]
            }
            }
        ]
        }

        messages = FlexSendMessage(alt_text="options", contents=messages)
        #メッセージ送信
        line_bot_api.push_message(user_id, messages=messages)

    if event.postback.data == "7-9":
        dis_d_sorted = sorted(dis_d.items(), key=lambda x:x[1])
        dis_d_top5 = dict(dis_d_sorted[6:9])
        dest_d_top5 = [dest_d[i] for i in dis_d_top5.keys()]
        hr_d_top5 = [hr_d[i] for i in list(dis_d_top5.keys())]
        paper_d_top5 = [paper_d[i] for i in dis_d_top5.keys()]
        electro_d_top5 = [electro_d[i] for i in dis_d_top5.keys()]
        style_d_top5 = [style_d[i] for i in dis_d_top5.keys()]

        lat = location_ltln[0]
        lon = location_ltln[1]
        link7 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[0][0])+","+str(dest_d_top5[0][1])+"&openExternalBrowser=1"
        link8 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[1][0])+","+str(dest_d_top5[1][1])+"&openExternalBrowser=1"
        link9 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[2][0])+","+str(dest_d_top5[2][1])+"&openExternalBrowser=1"
        
        messages = {
        "type": "carousel",
        "contents": [
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[0],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[0],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[0]+" 加熱式"+electro_d_top5[0],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[0],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link7
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[1],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "flex": 1,
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[1],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[1]+" 加熱式"+electro_d_top5[1],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[1],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "flex": 2,
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link8
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[2],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[2],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[2]+" 加熱式"+electro_d_top5[2],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[2],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link9
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "flex": 1,
                    "gravity": "center",
                    "action": {
                    "type": "postback",
                    "label": "次の３件を見る",
                    "data": "10-12"
                    }
                }
                ]
            }
            }
        ]
        }

        messages = FlexSendMessage(alt_text="options", contents=messages)
        #メッセージ送信
        line_bot_api.push_message(user_id, messages=messages)

    if event.postback.data == "10-12":
        dis_d_sorted = sorted(dis_d.items(), key=lambda x:x[1])
        dis_d_top5 = dict(dis_d_sorted[9:12])
        dest_d_top5 = [dest_d[i] for i in dis_d_top5.keys()]
        hr_d_top5 = [hr_d[i] for i in list(dis_d_top5.keys())]
        paper_d_top5 = [paper_d[i] for i in dis_d_top5.keys()]
        electro_d_top5 = [electro_d[i] for i in dis_d_top5.keys()]
        style_d_top5 = [style_d[i] for i in dis_d_top5.keys()]

        lat = location_ltln[0]
        lon = location_ltln[1]
        link10 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[0][0])+","+str(dest_d_top5[0][1])+"&openExternalBrowser=1"
        link11 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[1][0])+","+str(dest_d_top5[1][1])+"&openExternalBrowser=1"
        link12 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[2][0])+","+str(dest_d_top5[2][1])+"&openExternalBrowser=1"
        
        messages = {
        "type": "carousel",
        "contents": [
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[0],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[0],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[0]+" 加熱式"+electro_d_top5[0],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[0],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link10
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[1],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "flex": 1,
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[1],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[1]+" 加熱式"+electro_d_top5[1],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[1],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "flex": 2,
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link11
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[2],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[2],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[2]+" 加熱式"+electro_d_top5[2],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[2],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link12
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "flex": 1,
                    "gravity": "center",
                    "action": {
                    "type": "postback",
                    "label": "次の３件を見る",
                    "data": "13-15"
                    }
                }
                ]
            }
            }
        ]
        }

        messages = FlexSendMessage(alt_text="options", contents=messages)
        #メッセージ送信
        line_bot_api.push_message(user_id, messages=messages)

    if event.postback.data == "13-15":
        dis_d_sorted = sorted(dis_d.items(), key=lambda x:x[1])
        dis_d_top5 = dict(dis_d_sorted[12:15])
        dest_d_top5 = [dest_d[i] for i in dis_d_top5.keys()]
        hr_d_top5 = [hr_d[i] for i in list(dis_d_top5.keys())]
        paper_d_top5 = [paper_d[i] for i in dis_d_top5.keys()]
        electro_d_top5 = [electro_d[i] for i in dis_d_top5.keys()]
        style_d_top5 = [style_d[i] for i in dis_d_top5.keys()]

        lat = location_ltln[0]
        lon = location_ltln[1]
        link13 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[0][0])+","+str(dest_d_top5[0][1])+"&openExternalBrowser=1"
        link14 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[1][0])+","+str(dest_d_top5[1][1])+"&openExternalBrowser=1"
        link15 = "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[2][0])+","+str(dest_d_top5[2][1])+"&openExternalBrowser=1"
        
        messages = {
        "type": "carousel",
        "contents": [
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[0],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[0],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[0]+" 加熱式"+electro_d_top5[0],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[0],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link13
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[1],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "flex": 1,
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[1],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[1]+" 加熱式"+electro_d_top5[1],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[1],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "flex": 2,
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link14
                    }
                }
                ]
            }
            },
            {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": list(dis_d_top5.keys())[2],
                    "wrap": True,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "text",
                        "text": hr_d_top5[2],
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "flex": 0
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": "紙巻き"+paper_d_top5[2]+" 加熱式"+electro_d_top5[2],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": style_d_top5[2],
                    "wrap": True,
                    "size": "md",
                    "margin": "md",
                    "flex": 0
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "label": "マップを開く",
                    "uri": link15
                    }
                }
                ]
            }
            }
        ]
        }

        messages = FlexSendMessage(alt_text="options", contents=messages)
        #メッセージ送信
        line_bot_api.push_message(user_id, messages=messages)






if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)





"""
    elif event.postback.data == '喫煙所１' or event.postback.data == '喫煙所２' or event.postback.data == '喫煙所３'\
            or event.postback.data == '喫煙所４' or event.postback.data == '喫煙所５':
    #elif event.postback.label == "マップを開く":
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