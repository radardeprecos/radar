#!/bin/bash
# ============================================================
# Robô Radar Ninja v1 — Script de Execução 24/7
# Agendado via Manus Schedule ou Crontab
# ============================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Garantir que as pastas necessárias existam
mkdir -p logs
mkdir -p data/database

# Log de início
echo "[$(date)] 🚀 Iniciando ciclo de atualização Radar Ninja v1..." >> logs/execution.log

# Executar o orquestrador resiliente (pipeline completo)
python3 scripts/self_healing.py >> logs/execution.log 2>&1
PIPELINE_STATUS=$?

# Verificar status da execução
if [ $PIPELINE_STATUS -eq 0 ]; then
    echo "[$(date)] ✅ Pipeline concluído com sucesso." >> logs/execution.log

    # Fazer commit e push automático para o GitHub Pages
    git add -A
    CHANGED=$(git diff --cached --stat | tail -1)
    if [ -n "$CHANGED" ]; then
        git commit -m "🤖 Atualização automática — $(date '+%Y-%m-%d %H:%M')" >> logs/execution.log 2>&1
        # Sincronizar com remoto antes do push
        git pull --rebase origin main >> logs/execution.log 2>&1
        git push origin main >> logs/execution.log 2>&1
        if [ $? -eq 0 ]; then
            echo "[$(date)] 🚀 Site publicado no GitHub Pages com sucesso." >> logs/execution.log
        else
            echo "[$(date)] ⚠️ Falha no push para o GitHub." >> logs/execution.log
        fi
    else
        echo "[$(date)] ℹ️ Nenhuma alteração detectada. Push não necessário." >> logs/execution.log
    fi
else
    echo "[$(date)] ❌ Falha no pipeline. Verifique os logs detalhados." >> logs/execution.log
fi

# Limpeza de logs antigos (manter apenas os últimos 1000 linhas)
tail -n 1000 logs/execution.log > logs/execution.log.tmp && mv logs/execution.log.tmp logs/execution.log

echo "[$(date)] 🏁 Ciclo finalizado." >> logs/execution.log
