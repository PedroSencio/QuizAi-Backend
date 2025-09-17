
import os
from flask import Flask
from flask_cors import CORS
from openai import OpenAI


app = Flask(__name__)
CORS(app)

client = OpenAI(api_key='REMOVED_KEY')

prompt = """
Você é um gerador de quizzes educacionais. Recebe os seguintes parâmetros e gera um conjunto de questões no formato JSON.

Parâmetros:
- Assunto: {assunto}
- Quantidade de questões: {quantidade_questoes}
- Nível de dificuldade: {dificuldade}  # escolha entre 'fácil', 'médio', 'difícil'
- Tipos de questões permitidos: {tipos_permitidos}  # escolha entre 'multipla escolha' ou 'verdadeiro ou falso'
- Idioma: {idioma}

Regras:
1. As questões devem ser variadas e abordar diferentes aspectos do assunto solicitado.
2. Para "multipla escolha", forneça 3-5 alternativas e o índice da resposta correta.
3. Para "resposta curta", forneça um espaço para a resposta do usuário.
4. A resposta deve ser explicada de forma concisa.
5. O JSON gerado deve seguir a estrutura abaixo (não inclua texto fora do JSON):

Exemplo de saída JSON:

{{
  "questions": [
    {{
      "id": "1",
      "type": "multiple_choice",
      "prompt": "Qual é o valor de 7 × 8?",
      "choices": ["48", "54", "56", "64"],
      "answer_index": 2,
      "explanation": "7 × 8 = 56."
    }},
    {{
      "id": "2",
      "type": "true_false",
      "prompt": "A água é um bom condutor de eletricidade.",
      "choices": ["Verdadeiro", "Falso"],
      "answer_index": 1,
      "explanation": "Água pura não conduz eletricidade, mas a água com impurezas pode conduzir."
    }}
  ]
}}
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
    json_start = content.find('{')
    json_data = json.loads(content[json_start:])

    # Validação: garantir que answer_index corresponde à alternativa correta para múltipla escolha
    for q in json_data.get('questions', []):
      if q.get('type') == 'multiple_choice':
        choices = q.get('choices', [])
        answer_index = q.get('answer_index')
        explanation = q.get('explanation', '')
        # Tenta extrair a resposta correta da explicação
        import re
        match = re.search(r'(\d+|\w+|"[^"]+")', explanation)
        if match:
          correct_value = match.group(1)
          # Remove aspas se houver
          correct_value = correct_value.strip('"')
          # Procura o valor correto nas alternativas
          for idx, choice in enumerate(choices):
            if str(choice).strip() == correct_value:
              q['answer_index'] = idx
              break
    return jsonify(json_data)
  except Exception:
    return jsonify({'erro': 'Não foi possível gerar o quiz corretamente.', 'resposta': content}), 400

if __name__ == "__main__":
  app.run(debug=True)