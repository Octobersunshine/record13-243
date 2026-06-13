from flask import Flask, request, jsonify
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import copy


class VisaType(Enum):
    TOURIST = "旅游"
    BUSINESS = "商务"
    FAMILY = "探亲"


class MaterialCategory(Enum):
    IDENTITY = "身份证明"
    FINANCIAL = "财力证明"
    EMPLOYMENT = "工作证明"
    TRAVEL = "行程材料"
    RELATION = "关系证明"
    OTHER = "其他"


@dataclass
class MaterialItem:
    name: str
    category: MaterialCategory
    required: bool = True
    notes: str = ""


@dataclass
class ConsulateOverride:
    add: list = field(default_factory=list)
    modify: dict = field(default_factory=dict)


COMMON_MATERIALS = {
    VisaType.TOURIST: [
        MaterialItem("护照原件", MaterialCategory.IDENTITY, notes="有效期6个月以上，至少2页空白签证页"),
        MaterialItem("护照复印件", MaterialCategory.IDENTITY),
        MaterialItem("身份证复印件", MaterialCategory.IDENTITY),
        MaterialItem("户口本复印件", MaterialCategory.IDENTITY),
        MaterialItem("2寸白底照片", MaterialCategory.IDENTITY, notes="近6个月拍摄，具体规格见各国要求"),
        MaterialItem("签证申请表", MaterialCategory.IDENTITY, notes="如实填写，签名与护照一致"),
        MaterialItem("银行流水", MaterialCategory.FINANCIAL, notes="近6个月，余额建议5万元以上"),
        MaterialItem("存款证明", MaterialCategory.FINANCIAL, required=False, notes="建议5万元以上冻结3个月"),
        MaterialItem("在职证明", MaterialCategory.EMPLOYMENT, notes="含公司抬头、职位、薪资、准假说明"),
        MaterialItem("营业执照复印件", MaterialCategory.EMPLOYMENT, required=False, notes="加盖公章"),
        MaterialItem("往返机票预订单", MaterialCategory.TRAVEL),
        MaterialItem("酒店预订单", MaterialCategory.TRAVEL),
        MaterialItem("旅行计划行程单", MaterialCategory.TRAVEL),
        MaterialItem("旅行保险", MaterialCategory.TRAVEL, notes="覆盖全程，保额不低于3万欧元（申根）"),
    ],
    VisaType.BUSINESS: [
        MaterialItem("护照原件", MaterialCategory.IDENTITY, notes="有效期6个月以上，至少2页空白签证页"),
        MaterialItem("护照复印件", MaterialCategory.IDENTITY),
        MaterialItem("身份证复印件", MaterialCategory.IDENTITY),
        MaterialItem("户口本复印件", MaterialCategory.IDENTITY),
        MaterialItem("2寸白底照片", MaterialCategory.IDENTITY, notes="近6个月拍摄"),
        MaterialItem("签证申请表", MaterialCategory.IDENTITY),
        MaterialItem("银行流水", MaterialCategory.FINANCIAL, notes="近6个月"),
        MaterialItem("在职证明", MaterialCategory.EMPLOYMENT, notes="注明商务出行目的"),
        MaterialItem("营业执照复印件", MaterialCategory.EMPLOYMENT, notes="加盖公章"),
        MaterialItem("邀请函", MaterialCategory.OTHER, notes="由邀请方出具，注明邀请事由、停留时间等"),
        MaterialItem("商务往来证明", MaterialCategory.OTHER, required=False, notes="合同、往来邮件等"),
        MaterialItem("往返机票预订单", MaterialCategory.TRAVEL),
        MaterialItem("酒店预订单", MaterialCategory.TRAVEL),
        MaterialItem("旅行保险", MaterialCategory.TRAVEL, required=False),
    ],
    VisaType.FAMILY: [
        MaterialItem("护照原件", MaterialCategory.IDENTITY, notes="有效期6个月以上，至少2页空白签证页"),
        MaterialItem("护照复印件", MaterialCategory.IDENTITY),
        MaterialItem("身份证复印件", MaterialCategory.IDENTITY),
        MaterialItem("户口本复印件", MaterialCategory.IDENTITY),
        MaterialItem("2寸白底照片", MaterialCategory.IDENTITY),
        MaterialItem("签证申请表", MaterialCategory.IDENTITY),
        MaterialItem("银行流水", MaterialCategory.FINANCIAL, notes="近6个月"),
        MaterialItem("存款证明", MaterialCategory.FINANCIAL, required=False),
        MaterialItem("在职证明", MaterialCategory.EMPLOYMENT),
        MaterialItem("邀请函", MaterialCategory.OTHER, notes="由邀请人出具"),
        MaterialItem("邀请人身份证明", MaterialCategory.OTHER, notes="护照/身份证/居留许可复印件"),
        MaterialItem("亲属关系证明", MaterialCategory.RELATION, notes="公证书及认证件"),
        MaterialItem("邀请人资金担保", MaterialCategory.FINANCIAL, required=False, notes="如邀请人承担费用"),
        MaterialItem("往返机票预订单", MaterialCategory.TRAVEL),
        MaterialItem("旅行保险", MaterialCategory.TRAVEL, required=False),
    ],
}

COUNTRY_OVERRIDES = {
    "美国": {
        VisaType.TOURIST: [
            MaterialItem("DS-160确认页", MaterialCategory.IDENTITY, notes="在线填写后打印"),
            MaterialItem("预约确认页", MaterialCategory.IDENTITY),
            MaterialItem("签证费收据", MaterialCategory.OTHER),
            MaterialItem("房产证复印件", MaterialCategory.FINANCIAL, required=False),
            MaterialItem("车辆行驶证复印件", MaterialCategory.FINANCIAL, required=False),
            MaterialItem("结婚证复印件", MaterialCategory.IDENTITY, required=False),
        ],
        VisaType.BUSINESS: [
            MaterialItem("DS-160确认页", MaterialCategory.IDENTITY),
            MaterialItem("预约确认页", MaterialCategory.IDENTITY),
            MaterialItem("签证费收据", MaterialCategory.OTHER),
            MaterialItem("公司派遣信", MaterialCategory.EMPLOYMENT, notes="详细说明商务目的"),
        ],
        VisaType.FAMILY: [
            MaterialItem("DS-160确认页", MaterialCategory.IDENTITY),
            MaterialItem("预约确认页", MaterialCategory.IDENTITY),
            MaterialItem("签证费收据", MaterialCategory.OTHER),
            MaterialItem("I-134担保书", MaterialCategory.FINANCIAL, required=False, notes="邀请人填写"),
        ],
    },
    "日本": {
        VisaType.TOURIST: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY, notes="粘贴照片，签名"),
            MaterialItem("个人简历", MaterialCategory.OTHER, required=False),
            MaterialItem("个人所得税纳税证明", MaterialCategory.FINANCIAL, required=False, notes="近1年"),
        ],
        VisaType.BUSINESS: [
            MaterialItem("身元保证书", MaterialCategory.OTHER, notes="日方邀请单位出具"),
            MaterialItem("滞在预定表", MaterialCategory.TRAVEL, notes="详细日程安排"),
            MaterialItem("法人登记簿誊本", MaterialCategory.OTHER, required=False, notes="日方邀请单位"),
        ],
        VisaType.FAMILY: [
            MaterialItem("身元保证书", MaterialCategory.OTHER),
            MaterialItem("滞在预定表", MaterialCategory.TRAVEL),
            MaterialItem("招聘理由书", MaterialCategory.OTHER),
        ],
    },
    "英国": {
        VisaType.TOURIST: [
            MaterialItem("在线申请表打印件", MaterialCategory.IDENTITY),
            MaterialItem("预约确认信", MaterialCategory.IDENTITY),
            MaterialItem("肺结核检测证明", MaterialCategory.OTHER, notes="指定机构检测"),
        ],
        VisaType.BUSINESS: [
            MaterialItem("在线申请表打印件", MaterialCategory.IDENTITY),
            MaterialItem("预约确认信", MaterialCategory.IDENTITY),
            MaterialItem("肺结核检测证明", MaterialCategory.OTHER),
        ],
        VisaType.FAMILY: [
            MaterialItem("在线申请表打印件", MaterialCategory.IDENTITY),
            MaterialItem("预约确认信", MaterialCategory.IDENTITY),
            MaterialItem("肺结核检测证明", MaterialCategory.OTHER),
        ],
    },
    "申根": {
        VisaType.TOURIST: [
            MaterialItem("申根签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("机票预订单", MaterialCategory.TRAVEL, notes="全程机票"),
            MaterialItem("旅行保险", MaterialCategory.TRAVEL, notes="保额不低于3万欧元，覆盖所有申根国"),
            MaterialItem("行程单", MaterialCategory.TRAVEL, notes="详细到每天的行程"),
            MaterialItem("婚姻状况证明", MaterialCategory.IDENTITY, required=False),
        ],
        VisaType.BUSINESS: [
            MaterialItem("申根签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("旅行保险", MaterialCategory.TRAVEL, notes="保额不低于3万欧元"),
            MaterialItem("派遣信", MaterialCategory.EMPLOYMENT, notes="注明商务目的和停留时间"),
        ],
        VisaType.FAMILY: [
            MaterialItem("申根签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("旅行保险", MaterialCategory.TRAVEL, notes="保额不低于3万欧元"),
            MaterialItem("亲属关系公证书", MaterialCategory.RELATION, notes="需双认证"),
        ],
    },
    "澳大利亚": {
        VisaType.TOURIST: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY, notes="在线申请ImmiAccount"),
            MaterialItem("护照公证件", MaterialCategory.IDENTITY, required=False),
            MaterialItem("行程计划", MaterialCategory.TRAVEL, required=False),
        ],
        VisaType.BUSINESS: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("邀请信", MaterialCategory.OTHER),
            MaterialItem("商务背景材料", MaterialCategory.OTHER, required=False),
        ],
        VisaType.FAMILY: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("担保信", MaterialCategory.OTHER, notes="邀请人出具"),
            MaterialItem("关系证明公证书", MaterialCategory.RELATION),
        ],
    },
    "加拿大": {
        VisaType.TOURIST: [
            MaterialItem("临时居民签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("家庭信息表", MaterialCategory.IDENTITY),
            MaterialItem("教育和就业细节表", MaterialCategory.EMPLOYMENT),
            MaterialItem("旅行历史", MaterialCategory.OTHER, required=False, notes="过去10年旅行记录"),
        ],
        VisaType.BUSINESS: [
            MaterialItem("临时居民签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("家庭信息表", MaterialCategory.IDENTITY),
            MaterialItem("商务邀请函", MaterialCategory.OTHER),
        ],
        VisaType.FAMILY: [
            MaterialItem("临时居民签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("家庭信息表", MaterialCategory.IDENTITY),
            MaterialItem("邀请人的IMM5604表", MaterialCategory.OTHER),
        ],
    },
    "韩国": {
        VisaType.TOURIST: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("韩国入境申请书", MaterialCategory.IDENTITY),
            MaterialItem("个人所得税证明", MaterialCategory.FINANCIAL, required=False),
            MaterialItem("社保缴纳证明", MaterialCategory.FINANCIAL, required=False),
        ],
        VisaType.BUSINESS: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("韩国邀请函", MaterialCategory.OTHER),
            MaterialItem("韩国事业者登录证", MaterialCategory.OTHER, required=False),
        ],
        VisaType.FAMILY: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("亲属关系证明", MaterialCategory.RELATION, notes="公证书"),
            MaterialItem("邀请函", MaterialCategory.OTHER),
        ],
    },
    "泰国": {
        VisaType.TOURIST: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("往返机票确认单", MaterialCategory.TRAVEL),
            MaterialItem("不少于2万元存款证明", MaterialCategory.FINANCIAL),
        ],
        VisaType.BUSINESS: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("泰方邀请函", MaterialCategory.OTHER),
            MaterialItem("泰方公司营业执照", MaterialCategory.OTHER, required=False),
        ],
        VisaType.FAMILY: [
            MaterialItem("签证申请表", MaterialCategory.IDENTITY),
            MaterialItem("邀请函", MaterialCategory.OTHER),
            MaterialItem("关系证明", MaterialCategory.RELATION),
        ],
    },
}

SUPPORTED_COUNTRIES = list(COUNTRY_OVERRIDES.keys())

CONSULATE_OVERRIDES = {
    "美国": {
        "北京": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("护照原件彩色复印件", MaterialCategory.IDENTITY, notes="北京领事馆要求额外提供"),
                    MaterialItem("面签预约单（北京大使馆）", MaterialCategory.OTHER, notes="确认面签时间与地点"),
                    MaterialItem("DS-160提交确认页条形码页", MaterialCategory.IDENTITY, notes="北京要求清晰打印完整条形码"),
                ],
                modify={
                    "银行流水": {"notes": "近6个月，余额建议10万元以上，北京要求有明确工资标注", "required": True},
                    "在职证明": {"notes": "北京领事馆：必须包含准假人姓名、职位、联系方式并手写签字"},
                    "2寸白底照片": {"notes": "北京要求51mm×51mm，近期6个月内白底免冠电子版提交+纸质1张"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("赴美商务说明函", MaterialCategory.EMPLOYMENT, notes="北京要求详细说明商务目的、合作历史"),
                    MaterialItem("纳税证明", MaterialCategory.FINANCIAL, notes="公司近1年纳税记录，北京要求提供"),
                ],
                modify={
                    "公司派遣信": {"notes": "北京领事馆要求：注明费用承担方、美方合作方全称地址"},
                },
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("邀请人在美国的纳税证明", MaterialCategory.FINANCIAL, notes="北京要求提供近1年W2或税单"),
                ],
                modify={
                    "邀请人身份证明": {"notes": "北京要求：同时提供绿卡/签证+美国居住地址证明（水电账单）"},
                },
            ),
        },
        "上海": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：户籍/居住证/社保需在沪苏浙皖赣之一"),
                    MaterialItem("旅行计划英文版", MaterialCategory.TRAVEL, notes="上海要求英文详细行程"),
                ],
                modify={
                    "银行流水": {"notes": "近6个月，余额建议5万元以上，上海领区接受支付宝/微信辅助流水"},
                    "2寸白底照片": {"notes": "上海要求51mm×51mm，白底免冠，不可佩戴眼镜"},
                    "在职证明": {"notes": "上海领区：可接受英文版，需公司抬头纸打印盖章"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖赣户籍/居住证/社保"),
                ],
                modify={
                    "邀请函": {"notes": "上海要求：美方邀请信需说明过往合作关系及本次具体商务活动"},
                },
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖赣户籍/居住证/社保"),
                ],
                modify={
                    "亲属关系证明": {"notes": "上海接受：出生证明/户口本/结婚证原件作为关系证明，不一定需要公证"},
                },
            ),
        },
        "广州": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="广州领区：粤桂闽琼湘鄂户籍/居住证"),
                ],
                modify={
                    "在职证明": {"notes": "广州领区：如为个体经营者，需提供营业执照+近6个月对公流水"},
                },
            ),
        },
        "成都": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="成都领区：川滇黔渝藏户籍/居住证"),
                ],
            ),
        },
    },
    "日本": {
        "北京": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供北京居住证"),
                    MaterialItem("纳税证明", MaterialCategory.FINANCIAL, notes="北京领区要求年收入10万元以上纳税证明"),
                ],
                modify={
                    "个人所得税纳税证明": {"required": True, "notes": "北京领区必填，近1年，年收入10万以上"},
                    "银行流水": {"notes": "近6个月，月均入账≥8千元，北京领区要求较严"},
                    "在职证明": {"notes": "北京领区：必须注明入职时间、年薪、准假，盖人事章或公章"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供"),
                    MaterialItem("日本外务省认证邀请", MaterialCategory.OTHER, notes="部分情况需要"),
                ],
                modify={
                    "身元保证书": {"notes": "北京要求：日方邀请单位为上市公司或政府机构可简化"},
                },
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供"),
                ],
            ),
        },
        "上海": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖赣户籍或居住证"),
                    MaterialItem("全程酒店订单确认（含入住人姓名）", MaterialCategory.TRAVEL, notes="上海要求显示所有入住人姓名"),
                ],
                modify={
                    "银行流水": {"notes": "近6个月，月均入账≥5千元，上海领区接受理财/基金辅助证明"},
                    "个人所得税纳税证明": {"required": False, "notes": "上海领区选填，有则提高通过率"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("领区证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖赣户籍或居住证"),
                ],
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("领区证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖赣户籍或居住证"),
                    MaterialItem("在日亲属住民票", MaterialCategory.RELATION, notes="上海要求提供日本市役所出具的住民票原件"),
                ],
            ),
        },
        "广州": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区证明", MaterialCategory.IDENTITY, notes="广州领区：粤桂闽琼户籍或居住证"),
                    MaterialItem("紧急联系人信息表", MaterialCategory.OTHER, notes="广州领区要求填写"),
                ],
            ),
        },
    },
    "申根": {
        "北京": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供，北京领区覆盖华北"),
                    MaterialItem("机酒真实付款凭证", MaterialCategory.TRAVEL, notes="北京部分领馆要求已付款的确认单"),
                ],
                modify={
                    "旅行保险": {"notes": "北京要求：保额≥3万欧元，必须包含紧急医疗转运，保险日期需覆盖全程+首尾各2天"},
                    "银行流水": {"notes": "近3-6个月，余额≥5万元，北京要求有稳定的进出账记录"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供"),
                ],
                modify={
                    "派遣信": {"notes": "北京要求：含申请人信息、商务目的、停留时间、费用承担、担保按期回国，法人签字+盖章"},
                },
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供"),
                    MaterialItem("在申根亲属的房屋租赁合同", MaterialCategory.RELATION, required=False, notes="北京要求可提供佐证"),
                ],
                modify={
                    "亲属关系公证书": {"notes": "北京要求：必须经中国外交部和申根国驻华使馆双认证"},
                },
            ),
        },
        "上海": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖闽赣鲁户籍或居住证"),
                    MaterialItem("VAF申请表附加页", MaterialCategory.IDENTITY, required=False, notes="部分申根国上海领馆要求"),
                ],
                modify={
                    "旅行保险": {"notes": "上海要求：保额≥3万欧元，覆盖申根所有国家，保险生效需提前1天"},
                    "酒店预订单": {"notes": "上海要求：酒店确认单必须有酒店抬头、地址、盖章或邮箱确认"},
                    "银行流水": {"notes": "近3个月即可，余额≥3万元，上海接受信用卡账单辅助"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖闽赣鲁户籍或居住证"),
                ],
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖闽赣鲁户籍或居住证"),
                    MaterialItem("在申根亲属的护照首页+签证页复印件", MaterialCategory.RELATION, notes="上海要求提供"),
                ],
            ),
        },
    },
    "英国": {
        "北京": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供北京领区居住证明"),
                    MaterialItem("旧护照原件", MaterialCategory.IDENTITY, required=False, notes="北京建议提供，如有多次出入境记录有利于出签"),
                ],
                modify={
                    "肺结核检测证明": {"notes": "北京指定机构：北京国际SOS等，检测报告需英文原件，6个月内有效"},
                    "银行流水": {"notes": "近6个月，余额建议≥6万元，北京要求有稳定的工资入账标注"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供"),
                ],
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供"),
                    MaterialItem("在英亲属的银行流水", MaterialCategory.FINANCIAL, required=False, notes="北京建议提供，如邀请人承担费用"),
                ],
            ),
        },
        "上海": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖户籍或居住证"),
                    MaterialItem("签证申请校对表", MaterialCategory.IDENTITY, notes="上海签证中心要求填写核对表"),
                ],
                modify={
                    "肺结核检测证明": {"notes": "上海指定机构：上海瑞新等，6个月内有效"},
                    "银行流水": {"notes": "近3-6个月，余额≥4万元，上海接受理财/股票对账单作为辅助财力"},
                    "在职证明": {"notes": "上海领区：英文在职证明即可，需包含公司名称、地址、电话、准假信息"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖户籍或居住证"),
                ],
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖户籍或居住证"),
                ],
            ),
        },
    },
    "澳大利亚": {
        "北京": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍，北京领区覆盖华北东北"),
                    MaterialItem("彩色护照首页复印件", MaterialCategory.IDENTITY, notes="北京签证中心要求彩色扫描件"),
                ],
                modify={
                    "银行流水": {"notes": "近6个月，余额≥5万元，北京建议附加存款证明"},
                },
            ),
            VisaType.FAMILY: ConsulateOverride(
                add=[
                    MaterialItem("在澳亲属的VEVO签证状态查询", MaterialCategory.OTHER, notes="北京要求提供邀请人当前签证状态"),
                ],
            ),
        },
        "上海": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖鲁户籍或居住证"),
                ],
                modify={
                    "银行流水": {"notes": "近3-6个月，余额≥3万元，上海接受支付宝/微信流水辅助"},
                    "护照公证件": {"required": True, "notes": "上海领区要求护照彩色复印件或公证件"},
                },
            ),
        },
    },
    "加拿大": {
        "北京": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("临时居民访问签证申请核对表", MaterialCategory.OTHER, notes="北京签证中心要求提交IMM5484E表"),
                    MaterialItem("代理人信息表", MaterialCategory.OTHER, required=False, notes="如有代办需填写IMM5476E"),
                ],
                modify={
                    "银行流水": {"notes": "近6个月，余额≥8万元，北京建议提供房产证+车辆行驶证增加约束力"},
                },
            ),
            VisaType.FAMILY: ConsulateOverride(
                modify={
                    "邀请人的IMM5604表": {"required": True, "notes": "北京要求必须填写，详细说明邀请人与申请人关系、费用承担"},
                },
            ),
        },
        "上海": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖赣鄂户籍或居住证"),
                ],
                modify={
                    "银行流水": {"notes": "近6个月，余额≥5万元，上海接受基金/股票市值证明"},
                },
            ),
        },
    },
    "韩国": {
        "北京": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供北京领区居住证"),
                    MaterialItem("签证发给认定书", MaterialCategory.OTHER, required=False, notes="如有可简化材料"),
                ],
                modify={
                    "银行流水": {"notes": "近6个月，月均≥8千元，北京领区要求较严格"},
                    "个人所得税证明": {"required": True, "notes": "北京领区必填，近6个月，月税额≥200元"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供"),
                ],
            ),
        },
        "上海": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖户籍或居住证"),
                    MaterialItem("赴韩签证申请个人简历", MaterialCategory.OTHER, required=False, notes="上海领区建议提供"),
                ],
                modify={
                    "银行流水": {"notes": "近6个月，月均≥5千元，上海接受信用卡金卡/白金卡替代部分财力"},
                    "个人所得税证明": {"required": False, "notes": "上海选填，有则提高出签率；如持信用卡白金卡可免"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖户籍或居住证"),
                ],
            ),
        },
        "青岛": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="青岛领区：山东户籍或居住证"),
                ],
            ),
        },
    },
    "泰国": {
        "北京": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供北京居住证"),
                ],
                modify={
                    "不少于2万元存款证明": {"notes": "北京要求：冻结3个月以上，金额不低于2万元，需银行开具原件"},
                    "往返机票确认单": {"notes": "北京要求：必须为已出票的真实机票，英文或泰文"},
                    "酒店预订单": {"required": True, "notes": "北京领区要求提供全程酒店确认单"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("暂住证/居住证", MaterialCategory.IDENTITY, notes="非北京户籍需提供"),
                    MaterialItem("泰国外交部批文", MaterialCategory.OTHER, notes="商务签北京要求泰国劳工部或外交部批文"),
                ],
            ),
        },
        "上海": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖户籍或居住证"),
                    MaterialItem("英文版在职证明", MaterialCategory.EMPLOYMENT, notes="上海要求提供英文版在职证明"),
                ],
                modify={
                    "不少于2万元存款证明": {"notes": "上海要求：冻结1个月以上即可，可接受银行流水替代（近6个月月均≥5千）"},
                    "酒店预订单": {"required": False, "notes": "上海领区如通过旅行社代办可简化酒店预订单"},
                },
            ),
            VisaType.BUSINESS: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="上海领区：沪苏浙皖户籍或居住证"),
                ],
            ),
        },
        "广州": {
            VisaType.TOURIST: ConsulateOverride(
                add=[
                    MaterialItem("领区归属证明", MaterialCategory.IDENTITY, notes="广州领区：粤桂闽琼赣湘户籍或居住证"),
                ],
            ),
        },
    },
}


def _get_supported_consulates() -> list:
    result = set()
    for country_data in CONSULATE_OVERRIDES.values():
        result.update(country_data.keys())
    return sorted(result)


SUPPORTED_CONSULATES = _get_supported_consulates()

MATERIAL_ALIASES = {
    "护照原件": ["护照", "有效护照", "因私护照"],
    "护照复印件": ["护照副本", "护照复印", "护照扫描件", "护照首页复印件"],
    "护照原件彩色复印件": ["护照彩色复印件", "彩印护照"],
    "身份证复印件": ["身份证", "居民身份证复印件", "身份证正反面复印件"],
    "户口本复印件": ["户口本", "户口簿复印件", "全家户口本"],
    "2寸白底照片": ["2寸照片", "白底照片", "签证照片", "两寸照片", "2寸白底彩照"],
    "签证申请表": ["申请表", "签证表", "申请表格"],
    "DS-160确认页": ["DS160", "DS-160", "DS160确认页", "美国签证申请表"],
    "DS-160提交确认页条形码页": ["DS-160条形码", "DS160条形码页"],
    "预约确认页": ["预约单", "面签预约单", "预约信"],
    "面签预约单（北京大使馆）": ["北京面签预约单"],
    "签证费收据": ["签证费发票", "缴费凭证", "签证费凭证"],
    "银行流水": ["银行卡流水", "银行对账单", "工资流水", "银行账单", "账户流水", "储蓄卡流水"],
    "存款证明": ["银行存款证明", "存款单", "资金证明"],
    "不少于2万元存款证明": ["2万存款证明", "存款证明（2万）"],
    "房产证复印件": ["房产证", "不动产证", "房产证明"],
    "车辆行驶证复印件": ["行驶证", "车辆行驶证", "车本"],
    "结婚证复印件": ["结婚证", "婚姻证明"],
    "在职证明": ["在职信", "单位证明", "工作证明", "雇佣证明"],
    "营业执照复印件": ["营业执照", "公司营业执照", "工商执照"],
    "英文版在职证明": ["英文在职证明"],
    "公司派遣信": ["派遣函", "商务派遣信"],
    "赴美商务说明函": ["商务说明函", "赴美商务函"],
    "纳税证明": ["完税证明", "纳税凭证", "税务证明"],
    "个人所得税纳税证明": ["个税证明", "个税单", "纳税证明（个税）", "个人所得税完税证明"],
    "个人所得税证明": ["个税证明", "个税纳税证明"],
    "社保缴纳证明": ["社保证明", "社保缴费记录", "社保单"],
    "往返机票预订单": ["机票订单", "机票预订单", "往返机票", "机票行程单"],
    "往返机票确认单": ["机票确认单", "已出票机票"],
    "酒店预订单": ["酒店订单", "住宿证明", "酒店确认单", "住宿预订单"],
    "全程酒店订单确认（含入住人姓名）": ["全程酒店订单"],
    "旅行计划行程单": ["行程单", "旅行计划", "日程安排"],
    "滞在预定表": ["滞在表", "行程预定表"],
    "旅行保险": ["境外保险", "旅游保险", "医疗险", "申根保险"],
    "邀请函": ["邀请信", "邀请涵"],
    "商务往来证明": ["商务凭证", "合作证明"],
    "招聘理由书": ["招聘理由", "邀请理由书"],
    "身元保证书": ["身元保证", "日方保证书"],
    "法人登记簿誊本": ["法人誊本", "日本法人登记"],
    "个人简历": ["简历", "履历书"],
    "韩国入境申请书": ["入境申请书", "韩国入境表"],
    "签证发给认定书": ["签证认定书", "发给认定书"],
    "赴韩签证申请个人简历": ["赴韩简历"],
    "韩国邀请函": ["韩方邀请函"],
    "韩国事业者登录证": ["韩方事业者登录证"],
    "亲属关系证明": ["亲属证明", "关系证明"],
    "亲属关系公证书": ["亲属公证", "关系公证书"],
    "邀请人身份证明": ["邀请人身份证", "邀请人护照"],
    "邀请人资金担保": ["资金担保", "邀请人担保"],
    "I-134担保书": ["I-134", "I134表", "经济担保书"],
    "邀请人在美国的纳税证明": ["邀请人W2", "美国邀请人税单"],
    "在澳亲属的VEVO签证状态查询": ["VEVO查询", "VEVO状态"],
    "在英亲属的银行流水": ["邀请人银行流水（英）"],
    "在线申请表打印件": ["在线申请表"],
    "预约确认信": ["英国预约信"],
    "肺结核检测证明": ["肺结核证明", "体检证明", "TB检测"],
    "申根签证申请表": ["申根申请表"],
    "VAF申请表附加页": ["VAF附加页", "申根附加表"],
    "机票预订单": ["机票订单", "申根机票"],
    "行程单": ["申根行程单", "详细行程"],
    "婚姻状况证明": ["婚姻证明", "未婚证明"],
    "派遣信": ["申根派遣信"],
    "在申根亲属的护照首页+签证页复印件": ["申根亲属护照复印件"],
    "在申根亲属的房屋租赁合同": ["申根亲属租房合同"],
    "在日亲属住民票": ["住民票", "日本住民票"],
    "临时居民签证申请表": ["加拿大申请表", "IMM申请表"],
    "家庭信息表": ["加拿大家庭信息表"],
    "教育和就业细节表": ["教育就业表"],
    "旅行历史": ["过往旅行记录", "旧签证记录"],
    "商务邀请函": ["加方商务邀请函"],
    "邀请人的IMM5604表": ["IMM5604表", "加拿大邀请表"],
    "临时居民访问签证申请核对表": ["IMM5484E", "加拿大核对表"],
    "代理人信息表": ["IMM5476E", "代理表"],
    "签证申请校对表": ["英国校对表"],
    "旧护照原件": ["旧护照", "过期护照"],
    "彩色护照首页复印件": ["彩印护照首页", "彩色护照复印件"],
    "护照公证件": ["护照公证", "护照原件公证"],
    "行程计划": ["澳洲行程"],
    "邀请信": ["澳洲邀请信"],
    "商务背景材料": ["商务背景"],
    "担保信": ["澳洲担保信"],
    "关系证明公证书": ["澳方关系公证"],
    "领区归属证明": ["领区证明", "居住地证明", "暂住证/居住证", "暂住证", "居住证", "居住证明", "暂住证居住证", "暂住证和居住证", "领区归属证明"],
    "紧急联系人信息表": ["紧急联系人表"],
    "旅行计划英文版": ["英文行程单", "英文旅行计划"],
    "泰国外交部批文": ["泰国批文", "泰国劳工部批文"],
    "泰方邀请函": ["泰国邀请信"],
    "泰方公司营业执照": ["泰方营业执照"],
    "机酒真实付款凭证": ["机酒付款证明", "机票酒店付款凭证"],
    "签证申请个人简历": ["签证简历"],
}


def _normalize_material_name(name: str) -> str:
    if not name:
        return ""
    return "".join(ch for ch in name.strip() if not ch.isspace()).lower()


NAME_TO_CANONICAL = {}
for canonical, aliases in MATERIAL_ALIASES.items():
    key = _normalize_material_name(canonical)
    NAME_TO_CANONICAL[key] = canonical
    for alias in aliases:
        NAME_TO_CANONICAL[_normalize_material_name(alias)] = canonical


def _match_material_name(user_name: str) -> Optional[str]:
    if not user_name:
        return None
    norm = _normalize_material_name(user_name)
    if norm in NAME_TO_CANONICAL:
        return NAME_TO_CANONICAL[norm]

    for key, canonical in NAME_TO_CANONICAL.items():
        if norm and (norm in key or key in norm):
            return canonical
    return None


class VisaChecklistService:
    def _build_materials(self, country: str, visa_type: VisaType, consulate: Optional[str] = None):
        common = COMMON_MATERIALS.get(visa_type, [])
        extra = COUNTRY_OVERRIDES.get(country, {}).get(visa_type, [])

        all_materials = [copy.deepcopy(m) for m in common] + [copy.deepcopy(m) for m in extra]

        consulate_diff_summary = {"added": [], "modified": []}
        if consulate:
            override = CONSULATE_OVERRIDES.get(country, {}).get(consulate, {}).get(visa_type)
            if override:
                for new_item in override.add:
                    all_materials.append(copy.deepcopy(new_item))
                    consulate_diff_summary["added"].append(new_item.name)

                name_to_index = {}
                for idx, item in enumerate(all_materials):
                    name_to_index[item.name] = idx
                for mat_name, changes in override.modify.items():
                    if mat_name in name_to_index:
                        idx = name_to_index[mat_name]
                        original = all_materials[idx]
                        if "required" in changes:
                            original.required = changes["required"]
                        if "notes" in changes:
                            original.notes = changes["notes"]
                        consulate_diff_summary["modified"].append(mat_name)

        seen_names = set()
        unique_materials = []
        for item in all_materials:
            if item.name not in seen_names:
                seen_names.add(item.name)
                unique_materials.append(item)
        return unique_materials, consulate_diff_summary

    def get_checklist(self, country: str, visa_type_str: str, consulate: Optional[str] = None) -> dict:
        visa_type = self._parse_visa_type(visa_type_str)
        if visa_type is None:
            return {"error": f"不支持的签证类型: {visa_type_str}，请选择: 旅游/商务/探亲"}

        if country not in COUNTRY_OVERRIDES:
            return {"error": f"不支持的目的地国家: {country}，支持的国家: {', '.join(SUPPORTED_COUNTRIES)}"}

        if consulate:
            available_consulates = self.list_consulates_for_country(country)
            if consulate not in available_consulates:
                return {
                    "error": f"{country} 暂不支持 {consulate} 领事馆，该国家支持的领事馆: {', '.join(available_consulates)}",
                    "available_consulates": available_consulates,
                }

        unique_materials, consulate_diff_summary = self._build_materials(country, visa_type, consulate)

        categorized = {}
        for item in unique_materials:
            cat = item.category.value
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append({
                "name": item.name,
                "required": item.required,
                "notes": item.notes,
            })

        required_count = sum(1 for m in unique_materials if m.required)
        optional_count = sum(1 for m in unique_materials if not m.required)

        result = {
            "country": country,
            "visa_type": visa_type.value,
            "total_materials": len(unique_materials),
            "required_count": required_count,
            "optional_count": optional_count,
            "categories": categorized,
        }

        if consulate:
            result["consulate"] = consulate
            result["consulate_changes"] = {
                "added_count": len(consulate_diff_summary["added"]),
                "modified_count": len(consulate_diff_summary["modified"]),
                "added_items": consulate_diff_summary["added"],
                "modified_items": consulate_diff_summary["modified"],
            }

        return result

    def audit_materials(self, country: str, visa_type_str: str, user_materials: list, consulate: Optional[str] = None) -> dict:
        visa_type = self._parse_visa_type(visa_type_str)
        if visa_type is None:
            return {"error": f"不支持的签证类型: {visa_type_str}，请选择: 旅游/商务/探亲"}

        if country not in COUNTRY_OVERRIDES:
            return {"error": f"不支持的目的地国家: {country}，支持的国家: {', '.join(SUPPORTED_COUNTRIES)}"}

        if consulate:
            available_consulates = self.list_consulates_for_country(country)
            if consulate not in available_consulates:
                return {
                    "error": f"{country} 暂不支持 {consulate} 领事馆，该国家支持的领事馆: {', '.join(available_consulates)}",
                    "available_consulates": available_consulates,
                }

        unique_materials, consulate_diff_summary = self._build_materials(country, visa_type, consulate)

        def _canon(name):
            return _match_material_name(name) or name

        required_map = {}
        optional_map = {}
        for m in unique_materials:
            key = _canon(m.name)
            if m.required:
                required_map[key] = m
            else:
                optional_map[key] = m

        submitted_required = []
        submitted_optional = []
        missing_required = []
        missing_optional = []
        unrecognized = []
        matched_user = {}

        for user_mat in user_materials:
            if isinstance(user_mat, dict):
                name = user_mat.get("name", "").strip()
                provided = user_mat.get("provided", True)
            else:
                name = str(user_mat).strip()
                provided = True
            if not name:
                continue
            canonical = _match_material_name(name)
            if canonical is None:
                unrecognized.append({"name": name, "note": "未在标准材料清单中识别，请人工确认"})
                continue
            if canonical in matched_user:
                matched_user[canonical]["user_inputs"].append(name)
                continue
            info = {"canonical": canonical, "user_inputs": [name], "provided": provided}
            matched_user[canonical] = info

            if canonical in required_map:
                mat = required_map[canonical]
                entry = {"name": mat.name, "notes": mat.notes, "user_inputs": info["user_inputs"]}
                if provided:
                    submitted_required.append(entry)
                else:
                    missing_required.append({**entry, "note": "必填材料，用户标记为未提供"})
            elif canonical in optional_map:
                mat = optional_map[canonical]
                entry = {"name": mat.name, "notes": mat.notes, "user_inputs": info["user_inputs"]}
                if provided:
                    submitted_optional.append(entry)
                else:
                    missing_optional.append({**entry, "note": "选填材料，用户标记为未提供"})

        for canonical, mat in required_map.items():
            if canonical not in matched_user:
                missing_required.append({"name": mat.name, "notes": mat.notes, "note": "用户未提交此必填材料"})
        for canonical, mat in optional_map.items():
            if canonical not in matched_user:
                missing_optional.append({"name": mat.name, "notes": mat.notes, "note": "用户未提交此选填材料"})

        total_required = len(required_map)
        submitted_required_count = len(submitted_required)
        if total_required > 0:
            completion_rate = round(submitted_required_count / total_required * 100, 1)
        else:
            completion_rate = 100.0

        if completion_rate == 100.0:
            overall = "合格"
            overall_code = "pass"
        elif completion_rate >= 80.0:
            overall = "基本合格，缺少少量必填材料"
            overall_code = "almost"
        else:
            overall = "不合格，缺少较多必填材料"
            overall_code = "fail"

        warnings = []
        if unrecognized:
            warnings.append(f"有 {len(unrecognized)} 项材料未被识别，请人工核对")
        if missing_required:
            warnings.append(f"缺少 {len(missing_required)} 项必填材料")
        if missing_optional:
            warnings.append(f"缺少 {len(missing_optional)} 项选填材料（非必须，但有助于提高出签率）")

        suggestions = []
        for m in missing_required[:5]:
            suggestions.append(f"请尽快准备「{m['name']}」: {m['notes']}" if m["notes"] else f"请尽快准备「{m['name']}」")
        if len(missing_required) > 5:
            suggestions.append(f"另外还有 {len(missing_required) - 5} 项必填材料待准备")

        result = {
            "country": country,
            "visa_type": visa_type.value,
            "overall": overall,
            "overall_code": overall_code,
            "completion_rate": completion_rate,
            "summary": {
                "total_required": total_required,
                "submitted_required": submitted_required_count,
                "missing_required_count": len(missing_required),
                "total_optional": len(optional_map),
                "submitted_optional": len(submitted_optional),
                "missing_optional_count": len(missing_optional),
                "unrecognized_count": len(unrecognized),
            },
            "submitted_required": submitted_required,
            "submitted_optional": submitted_optional,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "unrecognized": unrecognized,
            "warnings": warnings,
            "suggestions": suggestions,
        }

        if consulate:
            result["consulate"] = consulate
        return result

    def _parse_visa_type(self, visa_type_str: str) -> Optional[VisaType]:
        mapping = {
            "旅游": VisaType.TOURIST,
            "商务": VisaType.BUSINESS,
            "探亲": VisaType.FAMILY,
            "tourist": VisaType.TOURIST,
            "business": VisaType.BUSINESS,
            "family": VisaType.FAMILY,
        }
        return mapping.get(visa_type_str.lower() if visa_type_str else "")

    def list_countries(self) -> list:
        return SUPPORTED_COUNTRIES

    def list_visa_types(self) -> list:
        return [vt.value for vt in VisaType]

    def list_consulates(self) -> list:
        return SUPPORTED_CONSULATES

    def list_consulates_for_country(self, country: str) -> list:
        country_data = CONSULATE_OVERRIDES.get(country, {})
        return sorted(country_data.keys())


app = Flask(__name__)
service = VisaChecklistService()


@app.route("/api/checklist", methods=["GET"])
def get_checklist():
    country = request.args.get("country", "").strip()
    visa_type = request.args.get("visa_type", "").strip()
    consulate = request.args.get("consulate", "").strip() or None

    if not country or not visa_type:
        return jsonify({
            "error": "请提供 country 和 visa_type 参数（consulate 可选）",
            "supported_countries": service.list_countries(),
            "supported_visa_types": service.list_visa_types(),
            "supported_consulates": service.list_consulates(),
            "example_without_consulate": "/api/checklist?country=美国&visa_type=旅游",
            "example_with_consulate": "/api/checklist?country=美国&visa_type=旅游&consulate=北京",
        }), 400

    result = service.get_checklist(country, visa_type, consulate)
    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route("/api/countries", methods=["GET"])
def list_countries():
    return jsonify({"countries": service.list_countries()})


@app.route("/api/visa_types", methods=["GET"])
def list_visa_types():
    return jsonify({"visa_types": service.list_visa_types()})


@app.route("/api/consulates", methods=["GET"])
def list_consulates():
    country = request.args.get("country", "").strip()
    if country:
        return jsonify({
            "country": country,
            "consulates": service.list_consulates_for_country(country),
        })
    return jsonify({"consulates": service.list_consulates()})


@app.route("/api/audit", methods=["POST"])
def audit_materials():
    data = request.get_json(silent=True) or {}
    country = (data.get("country") or "").strip()
    visa_type = (data.get("visa_type") or "").strip()
    consulate = (data.get("consulate") or "").strip() or None
    user_materials = data.get("materials") or []

    if not country or not visa_type:
        return jsonify({
            "error": "请在 JSON Body 中提供 country、visa_type 和 materials 数组（consulate 可选）",
            "request_schema": {
                "country": "string (必填)",
                "visa_type": "string (必填: 旅游/商务/探亲)",
                "consulate": "string (可选)",
                "materials": [
                    "string（材料名称）",
                    {"name": "string", "provided": "bool（默认true）"}
                ],
            },
            "example_request": {
                "country": "美国",
                "visa_type": "旅游",
                "consulate": "北京",
                "materials": [
                    "护照原件",
                    "身份证",
                    {"name": "银行流水", "provided": False},
                    "在职证明",
                    "我的神秘材料",
                ],
            },
        }), 400

    if not isinstance(user_materials, list) or not user_materials:
        return jsonify({"error": "materials 必须为非空数组"}), 400

    result = service.audit_materials(country, visa_type, user_materials, consulate)
    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "签证材料清单生成服务（支持领事馆差异 & 材料审核）",
        "endpoints": {
            "GET /api/checklist": "获取签证材料清单 (参数: country, visa_type, consulate[可选])",
            "POST /api/audit": "审核用户提交的材料是否齐全 (JSON Body)",
            "GET /api/countries": "获取支持的国家列表",
            "GET /api/visa_types": "获取支持的签证类型列表",
            "GET /api/consulates": "获取支持的领事馆列表 (可传 country 参数查看某国家)",
        },
        "examples": {
            "不指定领事馆": "/api/checklist?country=美国&visa_type=旅游",
            "北京领事馆": "/api/checklist?country=美国&visa_type=旅游&consulate=北京",
            "上海领事馆": "/api/checklist?country=日本&visa_type=旅游&consulate=上海",
            "材料审核": "POST /api/audit { country, visa_type, materials: [...] }",
            "查看日本支持的领事馆": "/api/consulates?country=日本",
        },
    })


def _print_audit_result(result):
    print(f"\n{'=' * 50}")
    title = f"  {result['country']}"
    if result.get("consulate"):
        title += f"·{result['consulate']}领事馆"
    title += f" - {result['visa_type']}签证 材料审核结果"
    print(title)
    s = result["summary"]
    print(f"  总体结论: {'✅' if result['overall_code']=='pass' else '⚠️' if result['overall_code']=='almost' else '❌'} {result['overall']}")
    print(f"  完成度: {result['completion_rate']}% (必填 {s['submitted_required']}/{s['total_required']}, 选填 {s['submitted_optional']}/{s['total_optional']})")
    if result["warnings"]:
        print("  提示:")
        for w in result["warnings"]:
            print(f"    · {w}")
    print(f"{'=' * 50}")

    if result["missing_required"]:
        print(f"\n❌ 缺少的必填材料（{len(result['missing_required'])}项）:")
        for m in result["missing_required"]:
            line = f"  · {m['name']}"
            if m.get("note"):
                line += f"  [{m['note']}]"
            if m.get("notes"):
                line += f"\n      说明: {m['notes']}"
            print(line)

    if result["submitted_required"]:
        print(f"\n✅ 已提供的必填材料（{len(result['submitted_required'])}项）:")
        for m in result["submitted_required"]:
            line = f"  · {m['name']}"
            if m.get("user_inputs") and m["user_inputs"] != [m["name"]]:
                line += f"  (你输入的: {'/'.join(m['user_inputs'])})"
            print(line)

    if result["missing_optional"]:
        print(f"\n🔲 未提交的选填材料（{len(result['missing_optional'])}项，有助于出签率）:")
        for m in result["missing_optional"][:10]:
            line = f"  · {m['name']}"
            if m.get("notes"):
                line += f"  ({m['notes'][:30]})"
            print(line)
        if len(result["missing_optional"]) > 10:
            print(f"  · 另外还有 {len(result['missing_optional'])-10} 项未显示...")

    if result["submitted_optional"]:
        print(f"\n✅ 已提供的选填材料（{len(result['submitted_optional'])}项）:")
        for m in result["submitted_optional"]:
            print(f"  · {m['name']}")

    if result["unrecognized"]:
        print(f"\n⚠️ 无法识别的材料（{len(result['unrecognized'])}项，请人工核对）:")
        for m in result["unrecognized"]:
            print(f"  · {m['name']}  ({m['note']})")

    if result["suggestions"]:
        print(f"\n💡 下一步建议:")
        for s in result["suggestions"]:
            print(f"  → {s}")
    print()


def cli_audit():
    print("=" * 50)
    print("       签证材料审核模式")
    print("=" * 50)

    country = input("\n请输入目的地国家: ").strip()
    if not country:
        print("未输入国家，返回主菜单")
        return
    visa_type = input("请输入签证类型 (旅游/商务/探亲): ").strip()
    if not visa_type:
        print("未输入签证类型，返回主菜单")
        return

    available_consulates = service.list_consulates_for_country(country)
    consulate = None
    if available_consulates:
        print(f"  该国家支持的领事馆: {', '.join(available_consulates)}")
        c = input("请输入领事馆 (直接回车忽略): ").strip()
        if c:
            consulate = c

    print("\n请输入你已准备好的材料，每行一项，输入空行结束:")
    print("  提示: 输入 材料名=未准备 或 材料名=否 可以标记为未提供")
    user_materials = []
    while True:
        line = input("  > ").strip()
        if not line:
            break
        if "=" in line:
            parts = line.split("=", 1)
            name = parts[0].strip()
            val = parts[1].strip().lower()
            provided = val not in ("否", "no", "n", "未准备", "missing", "0", "false")
            user_materials.append({"name": name, "provided": provided})
        else:
            user_materials.append(line)

    if not user_materials:
        print("未输入任何材料，返回主菜单")
        return

    result = service.audit_materials(country, visa_type, user_materials, consulate)
    if "error" in result:
        print(f"\n❌ {result['error']}")
        return
    _print_audit_result(result)


def cli():
    print("=" * 50)
    print("       签证材料清单生成服务")
    print("       支持领事馆差异 & 材料审核")
    print("=" * 50)

    while True:
        print("\n" + "-" * 50)
        print("请选择功能:")
        print("  1) 查询签证材料清单")
        print("  2) 审核我已准备的材料")
        print("  q) 退出")
        choice = input("请输入选项 (1/2/q): ").strip().lower()

        if choice == "q":
            print("再见！")
            break
        elif choice == "1":
            _cli_checklist()
        elif choice == "2":
            cli_audit()
        else:
            print("无效选项，请重新输入")


def _cli_checklist():
    countries = service.list_countries()
    print(f"\n支持的目的地国家: {', '.join(countries)}")

    visa_types = service.list_visa_types()
    print(f"支持的签证类型: {', '.join(visa_types)}")

    consulates = service.list_consulates()
    print(f"支持的领事馆: {', '.join(consulates)}（可选，不选则返回通用清单）")

    country = input("\n请输入目的地国家: ").strip()
    if not country:
        print("未输入国家，返回主菜单")
        return

    visa_type = input("请输入签证类型 (旅游/商务/探亲): ").strip()
    if not visa_type:
        print("未输入签证类型，返回主菜单")
        return

    available_consulates = service.list_consulates_for_country(country)
    consulate = None
    if available_consulates:
        print(f"  该国家支持的领事馆: {', '.join(available_consulates)}")
        c = input("请输入领事馆 (直接回车忽略): ").strip()
        if c:
            consulate = c

    result = service.get_checklist(country, visa_type, consulate)

    if "error" in result:
        print(f"\n❌ {result['error']}")
        return

    print(f"\n{'=' * 50}")
    title = f"  {result['country']}"
    if result.get("consulate"):
        title += f"·{result['consulate']}领事馆"
    title += f" - {result['visa_type']}签证 材料清单"
    print(title)
    print(f"  共 {result['total_materials']} 项 (必填 {result['required_count']} / 选填 {result['optional_count']})")
    if result.get("consulate_changes"):
        cc = result["consulate_changes"]
        print(f"  领事馆差异: 新增 {cc['added_count']} 项, 修改 {cc['modified_count']} 项")
        if cc["added_items"]:
            print(f"    新增: {', '.join(cc['added_items'])}")
        if cc["modified_items"]:
            print(f"    修改: {', '.join(cc['modified_items'])}")
    print(f"{'=' * 50}")

    for category, items in result["categories"].items():
        print(f"\n【{category}】")
        for item in items:
            tag = "✅必填" if item["required"] else "🔲选填"
            line = f"  {tag} {item['name']}"
            if item["notes"]:
                line += f"  ({item['notes']})"
            print(line)

    print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        cli()
    else:
        print("启动签证材料清单生成服务...")
        print("访问 http://127.0.0.1:5000/ 查看API说明")
        print("使用 --cli 参数启动命令行交互模式")
        app.run(debug=True, host="0.0.0.0", port=5000)
