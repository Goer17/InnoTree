# run in shell
python main.py --topic "Multi Agent System" \
    --model "custom-gpt-4o-mini" \
    --n_rollouts 10 \
    --n_trials 20 \
    --n_exp 3 \
    --n_results 5 \
    --arena \
    --sampling best

curl -X POST http://127.0.0.1:5000/start \
     -H "Content-Type: application/json" \
     -d '{
           "topic": "Object Detection",
           "api_key": "sk-AOlxKdZ9pbHPNDM721Bb9245183145BbA4E0F5583a9b2cAd",
           "base_url": "https://api.v3.cm/v1",
           "model": "gpt-4o-mini",
           "sampling_method": "best",
           "exploration_weight": 1.5,
           "n_trials": 15,
           "n_rollouts": 12,
           "n_expand": 3
         }'