
import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)
load_dotenv()
CORS(app)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

prompt = """
Você é um gerador de quizzes educacionais. Recebe os seguintes parâmetros e gera um conjunto de questões VARIADAS e DIVERSIFICADAS no formato JSON.

Parâmetros:
- Assunto: {assunto}
- Quantidade de questões: {quantidade_questoes}
- Nível de dificuldade: {dificuldade}  # escolha entre 'fácil', 'médio', 'difícil'
- Tipos de questões permitidos: {tipos_permitidos}  # escolha entre 'multipla escolha' ou 'verdadeiro ou falso'
- Idioma: {idioma}

Regras IMPORTANTES:
1. VARIE OS TIPOS DE PERGUNTAS - não repita o mesmo padrão
2. Para matemática: inclua operações diferentes (soma, subtração, multiplicação, divisão, precedência)
3. Para outras matérias: varie conceitos, definições, aplicações práticas
4. NUNCA repita perguntas similares (como "5+3*2", "10+2+5" - varie completamente)
5. Para múltipla escolha, forneça 4 alternativas diferentes e o índice correto (0-3)
6. O JSON deve seguir EXATAMENTE esta estrutura:

{{
  "questions": [
    {{
      "id": "1",
      "type": "multiple_choice",
      "prompt": "Pergunta variada aqui",
      "choices": ["opção1", "opção2", "opção3", "opção4"],
      "answer_index": 0,
      "explanation": "Explicação clara da resposta."
    }}
  ]
}}

IMPORTANTE: Para expressões matemáticas, calcule CORRETAMENTE seguindo a ordem de operações!
"""

from flask import request, jsonify

@app.route('/gerar_quiz', methods=['POST'])
def gerar_quiz():
  data = request.get_json()
  assunto = data.get('assunto')
  quantidade_questoes = data.get('quantidade_questoes')
  dificuldade = data.get('dificuldade')
  tipos_permitidos = data.get('tipos_permitidos')
  idioma = data.get('idioma')

  prompt_formatado = prompt.format(
    assunto=assunto,
    quantidade_questoes=quantidade_questoes,
    dificuldade=dificuldade,
    tipos_permitidos=tipos_permitidos,
    idioma=idioma
  )

  response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt_formatado}],
    max_tokens=1500,
    temperature=0.7,
  )
  content = response.choices[0].message.content.strip()
  try:
    # Tenta extrair o JSON da resposta
    import json
    json_data = json.loads(content)
    
    # Validação: corrigir respostas de expressões matemáticas
    for q in json_data.get('questions', []):
      if q.get('type') == 'multiple_choice':
        choices = q.get('choices', [])
        prompt_text = q.get('prompt', '')
        
        # Detecta se é uma expressão matemática simples
        import re
        math_match = re.search(r'(\d+(?:\s*[+\-*/]\s*\d+)+)', prompt_text)
        if math_match:
          expression = math_match.group(1).replace(' ', '')
          try:
            # Calcula o resultado correto da expressão
            correct_result = str(eval(expression))
            # Procura o resultado correto nas alternativas
            for idx, choice in enumerate(choices):
              if str(choice).strip() == correct_result:
                q['answer_index'] = idx
                # Atualiza a explicação com o cálculo correto
                q['explanation'] = f"Calculando: {expression} = {correct_result}"
                break
          except:
            pass  # Se der erro no eval, mantém o original
    
    return jsonify(json_data)
  except Exception:
    return jsonify({'erro': 'Não foi possível gerar o quiz corretamente.', 'resposta': content}), 400

if __name__ == "__main__":
  app.run(debug=True)