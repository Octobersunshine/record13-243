from flask import Flask, request, jsonify
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional


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


class VisaChecklistService:
    def get_checklist(self, country: str, visa_type_str: str) -> dict:
        visa_type = self._parse_visa_type(visa_type_str)
        if visa_type is None:
            return {"error": f"不支持的签证类型: {visa_type_str}，请选择: 旅游/商务/探亲"}

        if country not in COUNTRY_OVERRIDES:
            return {"error": f"不支持的目的地国家: {country}，支持的国家: {', '.join(SUPPORTED_COUNTRIES)}"}

        common = COMMON_MATERIALS.get(visa_type, [])
        extra = COUNTRY_OVERRIDES.get(country, {}).get(visa_type, [])

        all_materials = common + extra
        seen_names = set()
        unique_materials = []
        for item in all_materials:
            if item.name not in seen_names:
                seen_names.add(item.name)
                unique_materials.append(item)

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

        return {
            "country": country,
            "visa_type": visa_type.value,
            "total_materials": len(unique_materials),
            "required_count": required_count,
            "optional_count": optional_count,
            "categories": categorized,
        }

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


app = Flask(__name__)
service = VisaChecklistService()


@app.route("/api/checklist", methods=["GET"])
def get_checklist():
    country = request.args.get("country", "").strip()
    visa_type = request.args.get("visa_type", "").strip()

    if not country or not visa_type:
        return jsonify({
            "error": "请提供 country 和 visa_type 参数",
            "supported_countries": service.list_countries(),
            "supported_visa_types": service.list_visa_types(),
            "example": "/api/checklist?country=美国&visa_type=旅游",
        }), 400

    result = service.get_checklist(country, visa_type)
    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route("/api/countries", methods=["GET"])
def list_countries():
    return jsonify({"countries": service.list_countries()})


@app.route("/api/visa_types", methods=["GET"])
def list_visa_types():
    return jsonify({"visa_types": service.list_visa_types()})


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "签证材料清单生成服务",
        "endpoints": {
            "GET /api/checklist": "获取签证材料清单 (参数: country, visa_type)",
            "GET /api/countries": "获取支持的国家列表",
            "GET /api/visa_types": "获取支持的签证类型列表",
        },
        "example": "/api/checklist?country=美国&visa_type=旅游",
    })


def cli():
    print("=" * 50)
    print("       签证材料清单生成服务")
    print("=" * 50)

    countries = service.list_countries()
    print(f"\n支持的目的地国家: {', '.join(countries)}")

    visa_types = service.list_visa_types()
    print(f"支持的签证类型: {', '.join(visa_types)}")

    while True:
        print("-" * 50)
        country = input("\n请输入目的地国家 (输入 q 退出): ").strip()
        if country.lower() == "q":
            print("再见！")
            break

        visa_type = input("请输入签证类型 (旅游/商务/探亲): ").strip()
        if visa_type.lower() == "q":
            print("再见！")
            break

        result = service.get_checklist(country, visa_type)

        if "error" in result:
            print(f"\n❌ {result['error']}")
            continue

        print(f"\n{'=' * 50}")
        print(f"  {result['country']} - {result['visa_type']}签证 材料清单")
        print(f"  共 {result['total_materials']} 项 (必填 {result['required_count']} / 选填 {result['optional_count']})")
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
