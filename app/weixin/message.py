from time import time

from xml.etree import ElementTree as etree

class Message():
    def __init__(self):
        #self.message = message
        self.__properties = {}

    def generate_response_body(self):
        return self._generate_text_body()

    def _generate_text_body(self):
        home_web = "http://m.wecakes.com/shop"
        body = """<xml>
        <ToUserName><![CDATA[%s]]></ToUserName>
        <FromUserName><![CDATA[%s]]></FromUserName>
        <CreateTime>%d</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[您好，欢迎关注我们，请移步至 %s 选购]]></Content>
        </xml>""" % (self.__properties['FromUserName'], self.__properties['ToUserName'], int(time()), home_web)

        return body

    def _generate_location_body(self):
        body = """<xml>
                <ToUserName><![CDATA[%s]]></ToUserName>
                <FromUserName><![CDATA[%s]]></FromUserName>
                <CreateTime>%d</CreateTime>
                <MsgType><![CDATA[event]]></MsgType>
                <Event><![CDATA[location_select]]></Event>
                <EventKey><![CDATA[my_location]]></EventKey>
                <SendLocationInfo>
                    <Location_X><![CDATA[36.148392]]></Location_X>
                    <Location_Y><![CDATA[120.418907]]></Location_Y>
                    <Scale><![CDATA[15]]></Scale>
                    <Label><![CDATA[青岛市李沧区九水路227号一层南门卡诺烘焙]]></Label>
                    <Poiname><![CDATA[卡诺烘焙]]></Poiname>
                </SendLocationInfo>
            </xml>""" % (self.__properties['FromUserName'], self.__properties['ToUserName'], int(time()))

        return body

    def set_value(self, tag, value):
        self.__properties[tag] = value

    @property
    def type(self):
        return self.__properties['MsgType'];

    @property
    def event(self):
        return self.__properties['Event'];

def parse_message(xmlbody):
    root = etree.fromstring(xmlbody)

    message = Message()
    for e in root:
        print(e.tag, e.text)
        message.set_value(e.tag, e.text)

    return message
