import matplotlib.pyplot as plt
import numpy as np

# Dados dos modelos
tipos_tela = ['Grossa Manhã', 'Grossa Tarde', 'Fina Manhã', 'Fina Tarde']

# Modelo anterior: Regressão Linear
mae_anterior = [3.24, 3.38, 5.12, 4.62]
acc_anterior = [92.47, 91.80, 79.67, 85.35]

# Modelo atual: Rede Neural (MLP)
mae_atual = [2.24, 1.86, 2.96, 3.64]
acc_atual = [94.59, 95.92, 87.95, 87.37]

x = np.arange(len(tipos_tela))  # posição das barras
largura = 0.35  # largura das barras

fig, ax1 = plt.subplots(figsize=(12, 6))

# Gráfico de MAE (menor é melhor)
plt.subplot(1, 2, 1)
plt.bar(x - largura/2, mae_anterior, width=largura, label='MAE - Linear', color='salmon')
plt.bar(x + largura/2, mae_atual, width=largura, label='MAE - Neural', color='seagreen')
plt.xticks(x, tipos_tela, rotation=45)
plt.ylabel('MAE (Erro Médio Absoluto)')
plt.title('Comparação de MAE entre Modelos')
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Gráfico de Acurácia (maior é melhor)
plt.subplot(1, 2, 2)
plt.bar(x - largura/2, acc_anterior, width=largura, label='Acurácia - Linear', color='lightcoral')
plt.bar(x + largura/2, acc_atual, width=largura, label='Acurácia - Neural', color='mediumseagreen')
plt.xticks(x, tipos_tela, rotation=45)
plt.ylabel('Acurácia (%)')
plt.title('Comparação de Acurácia entre Modelos')
plt.ylim(70, 100)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()
