"""
Camada de IA (Fase 3)
=====================
Fala com um servidor local pela API **compatível com OpenAI** (LM Studio agora,
Ollama depois — sem reprogramar). Toda a lógica depende da interface ``MotorIA``,
nunca do servidor direto: por isso os testes rodam com um ``MotorIAFake``.

AVISO IMPORTANTE sobre o fake:
O ``MotorIAFake`` valida o ENCANAMENTO (o texto entra, é parseado e volta como
estrutura), **não** a QUALIDADE da IA. Consertar 'DE SODORANTE'→Desodorante,
pôr acentos, reordenar, categoria e +18, e o OCR — isso só se prova com o
modelo real (Qwen no LM Studio). A conciliação (embeddings+fuzzy) se valida sem
o modelo, pois só o "juiz" dos ambíguos usa a IA.
"""
