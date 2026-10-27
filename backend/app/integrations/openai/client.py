import json
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.schemas import AIAnalysisResult


SYSTEM_PROMPT = """أنت محلل تجربة عملاء دقيق. حلل المراجعة فقط من البيانات المقدمة.
افصل دائمًا بين ما ذكره العميل، واستنتاج النموذج، والمعلومة الداخلية المؤكدة.
لا تعتبر ذكر موظف إثباتًا على مسؤوليته. لا تطابق موظفًا اعتمادًا على الجنسية وحدها.
إذا لم تتوفر أدلة كافية، اجعل السبب الجذري غير مؤكد وقلّل الثقة.
استخدم تصنيفات المؤسسة المقدمة ولا تخترع حقائق أو اتجاهات."""


class OpenAIAnalyzer:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        key = api_key or settings.openai_api_key
        if not key:
            raise RuntimeError("OPENAI_API_KEY is required")
        from openai import OpenAI

        self.client = OpenAI(api_key=key)
        self.model = model or settings.openai_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
    def analyze(self, payload: dict[str, Any]) -> AIAnalysisResult:
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            text_format=AIAnalysisResult,
        )
        if response.output_parsed is None:
            raise ValueError("OpenAI returned no structured analysis")
        return response.output_parsed

