from eralchemy2 import render_er
from app.domain.models import Base

output_file = 'MER_ELAION_SIRAC.md'

# Gera o diagrama no formato Mermaid ER (Salva como texto/Markdown)
render_er(Base, output_file, mode='mermaid_er')

# Pós-processamento para inserir 'direction LR' no diagrama Mermaid
with open(output_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Insere a direção logo após a tag "erDiagram"
updated_content = content.replace("erDiagram", "erDiagram\n    direction LR")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("Diagrama gerado com sucesso com a orientação horizontal (LR)!")
