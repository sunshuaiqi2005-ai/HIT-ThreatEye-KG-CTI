from fastapi import APIRouter, File, UploadFile
import PyPDF2
from io import BytesIO

router = APIRouter()

@router.post("/api/extract_pdf")
async def extract_pdf(file: UploadFile = File(...)):
    # 读取上传的 PDF 文件
    content = await file.read()

    try:
        # 使用 PyPDF2 读取 PDF 内容
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # 返回提取的文本
        return {"text": text}
    except Exception as e:
        return {"error": f"PDF 解析失败: {str(e)}"}

