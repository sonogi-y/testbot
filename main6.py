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

    if text == "吸いたい！":
        # DBへの保存
        try:
            sql = "select * from " +  REMOTE_DB_TB +  " where user_id='"+str(user_id)+"';"
            c.execute(sql)
            ret = c.fetchall()

            if len(ret) == 0:
                status=1
                sql="insert into "+REMOTE_DB_TB+ " values ('"+str(user_id)+"','"+str(display_name)+"','none', 'none', 'none', 'none');"
                
                # メッセージの送信
                buttons_template = ButtonsTemplate(title='初めまして！', \
                    text='あなたについて少し教えてくれますか？', \
                    actions=[PostbackAction(label='あなたについての質問に答える', data='answer'),PostbackAction(label='やっぱりやめておく', data='no')])
                template_message = TemplateSendMessage(alt_text='welcome', template=buttons_template)
                line_bot_api.reply_message(event.reply_token, template_message)

            elif len(ret) == 1:
                sql_status = "select * from " +  REMOTE_DB_TB3 +  " where user_id='"+str(user_id)+"';"
                c.execute(sql_status)
                ret_status = c.fetchall()
                #status=str(int(ret_status[0][0])+1)
                dt_now = str(datetime.datetime.now())[0:10]
                ret_df = pd.DataFrame(ret_status)
                latest = str(max(ret_df[1]))[0:10]
                if dt_now == latest:
                    status = len([str(i) for i in ret_df[1] if latest in str(i)])+1
                elif dt_now != latest:
                    status = 1
                #status = str(len(ret_status)+1)
                #sql="update "+REMOTE_DB_TB+ " set status = '"+str(status)+"' WHERE user_id = '"+str(user_id)+"';"

                # メッセージの送信
                buttons_template = ButtonsTemplate(title='おかえりなさい！', \
                    text='今日は'+str(status)+"回ご利用しています", \
                    actions=[PostbackAction(label='喫煙タイプを選ぶ', data='chat'),PostbackAction(label='やっぱりやめておく', data='no')])
                template_message = TemplateSendMessage(alt_text='welcomeback', template=buttons_template)
                line_bot_api.reply_message(event.reply_token, template_message)

            c.execute(sql)
            conn.commit()
        finally:
            pass
        #    conn.close()
        #    c.close()

    elif text == "やめておく":
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="我慢できたあなたはえらい！"))

    elif text == "データ":
        line_bot_api.reply_message(
            event.reply_token,ImageSendMessage(
            #original_content_url="https://1.bp.blogspot.com/-eaDZ7sDP9uY/Xhwqlve5SUI/AAAAAAABXBo/EcI2C2vim7w2WV6EYy3ap0QLirX7RPohgCNcBGAsYHQ/s400/pose_syanikamaeru_man.png",
            #preview_image_url="https://1.bp.blogspot.com/-eaDZ7sDP9uY/Xhwqlve5SUI/AAAAAAABXBo/EcI2C2vim7w2WV6EYy3ap0QLirX7RPohgCNcBGAsYHQ/s400/pose_syanikamaeru_man.png"))
            original_content_url="https://uploda1.ysklog.net/uploda/7dc2bc1fbd.png",
            preview_image_url="https://uploda1.ysklog.net/uploda/7dc2bc1fbd.png"))




#######################################################




@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    text = event.message.address
    lat = event.message.latitude
    lon = event.message.longitude
    user_id = event.source.user_id

    sql = "select MAX(date) from "+REMOTE_DB_TB3+ " WHERE user_id = '"+str(user_id)+"';"
    c.execute(sql)
    ret = c.fetchall()
    latest = str(ret[0][0])

    sql="update "+REMOTE_DB_TB3+ " set lat = '"+str(lat)+"' WHERE user_id = '"+str(user_id)+"' and date = '"+latest+"';"
    #sql="update "+REMOTE_DB_TB3+ " set preference1 = '"+preference1+"' WHERE user_id = '"+str(user_id)+"';"
    c.execute(sql)
    conn.commit()

    sql="update "+REMOTE_DB_TB3+ " set long = '"+str(lon)+"' WHERE user_id = '"+str(user_id)+"' and date = '"+latest+"';"
    #sql="update "+REMOTE_DB_TB3+ " set preference1 = '"+preference1+"' WHERE user_id = '"+str(user_id)+"';"
    c.execute(sql)
    conn.commit()

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
             #"comgooglemaps://?saddr=新宿駅&daddr=35.658581,139.745433",\
                "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[1][0])+","+str(dest_d_top5[1][1]),\
                "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[2][0])+","+str(dest_d_top5[2][1]),\
                "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[3][0])+","+str(dest_d_top5[3][1]),\
                "https://www.google.com/maps/dir/?api=1&origin="+str(lat)+","+str(lon)+"&destination="+str(dest_d_top5[4][0])+","+str(dest_d_top5[4][1]),
            )
        )
    )
    ]
    message_template = CarouselTemplate(columns=carousel_columns)
    line_bot_api.push_message(
        to=user_id,
        messages=TemplateSendMessage(alt_text='carousel template', template=message_template)
    )



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

    if event.postback.data == 'no':
        sql = "delete from " +  REMOTE_DB_TB +  " where user_id='"+str(user_id)+"';"
        c.execute(sql)
        conn.commit()


        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='帰ってしまいますか？もしよければ理由をお聞かせください。',
                    quick_reply=QuickReply(
                        items=[
                        QuickReplyButton(
                            action=PostbackAction(label="間違え", data="wrong_room")
                        ),
                        QuickReplyButton(
                            action=PostbackAction(label="待てない", data="long_que")
                        ),
                        QuickReplyButton(
                            action=PostbackAction(label="吸えない状況になった", data="uncomfortable_situation")
                        ),
                    ])))
    
    elif event.postback.data == "wrong_room" or event.postback.data == "long_que" or event.postback.data == "uncomfortable_situation" or event.postback.data == "not_ask":
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="我慢できたあなたはえらい！"))


    elif event.postback.data == 'regular' or event.postback.data == "electric":
        #sql = "select * from "+REMOTE_DB_TB3+ " WHERE user_id = '"+str(user_id)+"';"
        sql = "select MAX(date) from "+REMOTE_DB_TB3+ " WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        ret = c.fetchall()
        latest = str(ret[0][0])

        preference1 = event.postback.data
        sql="update "+REMOTE_DB_TB3+ " set preference1 = '"+preference1+"' WHERE user_id = '"+str(user_id)+"' and date = '"+latest+"';"
        #sql="update "+REMOTE_DB_TB3+ " set preference1 = '"+preference1+"' WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        conn.commit()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='喫煙所ですか？カフェですか？',
                quick_reply=QuickReply(
                    items=[
                    QuickReplyButton(
                        action=PostbackAction(label="喫煙所", data="smoking_area")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="カフェ・レストラン", data="cafe")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="バー・居酒屋", data="bar"),
                    )
                ])))
    elif event.postback.data == "smoking_area" or event.postback.data == "cafe" or event.postback.data == "bar":
        sql = "select MAX(date) from "+REMOTE_DB_TB3+ " WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        ret = c.fetchall()
        latest = str(ret[0][0])

        preference2 = event.postback.data
        sql="update "+REMOTE_DB_TB3+ " set preference2 = '"+preference2+"' WHERE user_id = '"+str(user_id)+"' and date = '"+latest+"';"
        #sql="update "+REMOTE_DB_TB3+ " set preference1 = '"+preference1+"' WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        conn.commit()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='ご希望の形態はございますか？',
                quick_reply=QuickReply(
                    items=[
                    QuickReplyButton(
                        action=PostbackAction(label="分煙", data="separated")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="席で吸える", data="table")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="外で吸える", data="outdoor"),
                    )
                ])))


    elif event.postback.data == 'answer':
        #sex = "female"
        #ここでDBの更

        #あとでここ変更
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='性別を教えてください',
                quick_reply=QuickReply(
                    items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女性", data="female")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男性", data="male")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="その他", data="others")
                    )
                ])))

    elif event.postback.data == 'female' or event.postback.data == 'male':
        sex=event.postback.data
        sql="update "+REMOTE_DB_TB+ " set sex = '"+str(sex)+"' WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        conn.commit()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='職業を教えてください',
                quick_reply=QuickReply(
                    items=[
                    QuickReplyButton(
                        action=PostbackAction(label="有職", data="employed")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="無職", data="unemployed")
                    ),
                ])))

    elif event.postback.data == "employed" or event.postback.data == "unemployed":
        job=event.postback.data
        sql="update "+REMOTE_DB_TB+ " set job = '"+str(job)+"' WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        conn.commit()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='電子タバコは吸われますか？',
                quick_reply=QuickReply(
                    items=[
                    QuickReplyButton(
                        action=PostbackAction(label="吸わない", data="regular_only")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="吸う", data="electric_too")
                    ),
                ])))

    elif event.postback.data == "regular_only" or event.postback.data == "electric_too":
        electric=event.postback.data
        sql="update "+REMOTE_DB_TB+ " set electric = '"+str(electric)+"' WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        conn.commit()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='成人してますか？',
                quick_reply=QuickReply(
                    items=[
                    QuickReplyButton(
                        action=PostbackAction(label="未成年", data="young")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="成人", data="old")
                    ),
                ])))

    elif event.postback.data == 'old' or event.postback.data == "chat":
        if event.postback.data == "old":
            age=event.postback.data
            sql="update "+REMOTE_DB_TB+ " set age = '"+str(age)+"' WHERE user_id = '"+str(user_id)+"';"
            c.execute(sql)
            conn.commit()
        else:
            pass

        sql2 = "insert into "+REMOTE_DB_TB3+ " values ('"+str(user_id)+"',current_timestamp,'none', 'none', 'none', 'none','none','none');"
        c.execute(sql2)
        conn.commit()
        #相談番号別テーブル
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='今の気分をお伺いします！普通タバコですか？電子タバコですか？',
                quick_reply=QuickReply(
                    items=[
                    QuickReplyButton(
                        action=PostbackAction(label="普通タバコ", data="regular")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="電子タバコ", data="electric")
                    )
                ])))

    elif event.postback.data == 'young':
        age=event.postback.data
        sql="update "+REMOTE_DB_TB+ " set age = '"+str(age)+"' WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        conn.commit()
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="ごめんなさい。未成年の方はご利用いただけません。"))


    elif event.postback.data == 'separated' or event.postback.data == "table" or event.postback.data == "outdoor":  
        sql = "select MAX(date) from "+REMOTE_DB_TB3+ " WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        ret = c.fetchall()
        latest = str(ret[0][0])

        preference3 = event.postback.data
        sql="update "+REMOTE_DB_TB3+ " set preference3 = '"+preference3+"' WHERE user_id = '"+str(user_id)+"' and date = '"+latest+"';"
        #sql="update "+REMOTE_DB_TB3+ " set preference1 = '"+preference1+"' WHERE user_id = '"+str(user_id)+"';"
        c.execute(sql)
        conn.commit()

        buttons_template = ButtonsTemplate(title="お近くで喫煙できる場所をお探しします！", \
            #（ここでトピックに合わせて、ある程度用意した定型文を投げる）
            text='現在地を教えていただけますか？', \
            actions=[PostbackAction(label='頼む', data='ask'),PostbackAction(label='やっぱりやめる', data='not_ask')])
        template_message = TemplateSendMessage(alt_text='connecting', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
        

    elif event.postback.data == 'ask' or event.postback.data == 'wrong_address':
        line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text="位置情報を送ってください"),
                    TextSendMessage(text='line://nv/location'),
                ]
            )
    elif event.postback.data == "slacking":
        # webhookURLを指定
        webhook_url = "https://hooks.slack.com/services/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"

        # 送信するテキストを定義

        # Slackに送信する
        requests.post(webhook_url, data = json.dumps({
            "text": display_name+"が今からタバコすいます"
        }));



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)