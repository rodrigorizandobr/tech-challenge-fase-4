#!/usr/bin/env python3
"""
Script de teste para a API Cripto Prediction
Testa se a API consegue carregar modelos do S3 e fazer predições
"""

import requests
import json
import time
import sys

def test_api_health(base_url):
    """Testa o endpoint de health"""
    print("🔍 Testando health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check OK - Status: {data['status']}")
            print(f"   Modelos carregados: {data['models_loaded']}")
            print(f"   Total de modelos: {data['total_models']}")
            return True
        else:
            print(f"❌ Health check falhou - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False

def test_models_endpoint(base_url):
    """Testa o endpoint de modelos"""
    print("\n📊 Testando endpoint de modelos...")
    try:
        response = requests.get(f"{base_url}/models", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Models endpoint OK")
            print(f"   Total de modelos: {data['total_models']}")
            print(f"   Modelos: {data['models']}")
            return True
        else:
            print(f"❌ Models endpoint falhou - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no models endpoint: {e}")
        return False

def test_prediction(base_url, symbol="BTC"):
    """Testa o endpoint de predição"""
    print(f"\n🔮 Testando predição para {symbol}...")
    try:
        response = requests.get(f"{base_url}/symbol/{symbol}", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Predição OK para {symbol}")
            print(f"   Total de modelos: {data['total_modelos']}")
            print(f"   Modelos com predições: {list(data['modelos'].keys())}")
            
            # Mostra algumas predições
            for model_name, prediction in data['modelos'].items():
                if 'predicao' in prediction:
                    pred_value = prediction['predicao']
                    pred_type = prediction.get('tipo', 'unknown')
                    print(f"   {model_name}: {pred_value} ({pred_type})")
            
            return True
        else:
            print(f"❌ Predição falhou - Status: {response.status_code}")
            if response.text:
                print(f"   Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro na predição: {e}")
        return False

def test_reload_models(base_url):
    """Testa o endpoint de reload"""
    print("\n🔄 Testando reload de modelos...")
    try:
        response = requests.get(f"{base_url}/reload", timeout=120)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Reload OK")
            print(f"   Total de modelos: {data['total_models']}")
            print(f"   Modelos: {data['models']}")
            return True
        else:
            print(f"❌ Reload falhou - Status: {response.status_code}")
            if response.text:
                print(f"   Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro no reload: {e}")
        return False

def main():
    """Função principal de teste"""
    if len(sys.argv) < 2:
        print("Uso: python test_api.py <base_url>")
        print("Exemplo: python test_api.py http://localhost:8000")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    print(f"🚀 Testando API em: {base_url}")
    
    # Lista de testes
    tests = [
        ("Health Check", lambda: test_api_health(base_url)),
        ("Models Endpoint", lambda: test_models_endpoint(base_url)),
        ("Prediction BTC", lambda: test_prediction(base_url, "BTC")),
        ("Prediction ETH", lambda: test_prediction(base_url, "ETH")),
        ("Reload Models", lambda: test_reload_models(base_url)),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 Executando: {test_name}")
        print(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} - PASSOU")
            else:
                print(f"❌ {test_name} - FALHOU")
                
        except Exception as e:
            print(f"❌ {test_name} - ERRO: {e}")
            results.append((test_name, False))
        
        time.sleep(2)  # Pausa entre testes
    
    # Resumo final
    print(f"\n{'='*50}")
    print("📋 RESUMO DOS TESTES")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! API está funcionando corretamente.")
        sys.exit(0)
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs da API.")
        sys.exit(1)

if __name__ == "__main__":
    main() 