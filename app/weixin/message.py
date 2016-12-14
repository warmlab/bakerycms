from time import time

from xml.etree import ElementTree as etree

class Message():
    def __init__(self):
        #self.message = message
        self.__properties = {}
        self.member = None

    def generate_response_body(self):
        if self.event == 'CLICK' and self.event_key == 'my_location':
            return self._generate_location_body()
        return self._generate_text_body()

    def _generate_text_body(self):
        home_web = "http://m.wecakes.com"
        body = """<xml>
        <ToUserName><![CDATA[%s]]></ToUserName>
        <FromUserName><![CDATA[%s]]></FromUserName>
        <CreateTime>%d</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[亲爱的%s，您好，欢迎关注我们，请致电18053214078，0532-58806365订购。%s 正在积极装修中，敬请期待]]></Content>
        </xml>""" % (self.member.nickname if self.member and self.member.nickname else "",
                     self.__properties['FromUserName'], self.__properties['ToUserName'],
                     int(time()), home_web)

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

        print(body)

        return body

    def set_value(self, tag, value):
        self.__properties[tag] = value

    def get_value(self, tag):
        return self.__properties.get(tag)

    @property
    def type(self):
        return self.__properties['MsgType'];

    @property
    def event(self):
        return self.__properties.get('Event');

    @property
    def event_key(self):
        return self.__properties.get('EventKey')

def parse_message(xmlbody):
    root = etree.fromstring(xmlbody)

    message = Message()
    for e in root:
        print(e.tag, e.text)
        message.set_value(e.tag, e.text)

    return message
