#!/usr/bin/env python3
"""
Script de teste para o mock do Heterium (HET)
Testa se a API consegue fazer predições com dados mock
"""

import requests
import json
import time
import sys

def test_het_mock(base_url):
    """Testa o mock do Heterium"""
    print("🎭 Testando mock do Heterium (HET)...")
    
    try:
        # Teste de predição para HET
        response = requests.get(f"{base_url}/symbol/HET", timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Mock do HET funcionando!")
            print(f"   Ativo: {data['ativo']}")
            print(f"   Timestamp: {data['timestamp']}")
            print(f"   Total de modelos: {data['total_modelos']}")
            
            # Mostra predições
            if 'modelos' in data:
                print(f"   Modelos com predições:")
                for model_name, prediction in data['modelos'].items():
                    if 'predicao' in prediction:
                        pred_value = prediction['predicao']
                        pred_type = prediction.get('tipo', 'unknown')
                        print(f"     📊 {model_name}: {pred_value} ({pred_type})")
                        
                        if 'probabilidade' in prediction:
                            prob = prediction['probabilidade']
                            print(f"        Probabilidade: {prob:.4f}")
            
            return True
        else:
            print(f"❌ Mock do HET falhou - Status: {response.status_code}")
            if response.text:
                print(f"   Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste do mock HET: {e}")
        return False

def test_health_with_het(base_url):
    """Testa health check com HET"""
    print("\n🔍 Testando health check...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check OK")
            print(f"   Status: {data['status']}")
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
    """Testa endpoint de modelos"""
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

def test_multiple_symbols(base_url):
    """Testa múltiplos símbolos incluindo HET"""
    print("\n🔄 Testando múltiplos símbolos...")
    
    symbols = ["HET", "BTC", "ETH"]
    results = {}
    
    for symbol in symbols:
        try:
            response = requests.get(f"{base_url}/symbol/{symbol}", timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {symbol}: OK")
                results[symbol] = True
            else:
                print(f"❌ {symbol}: Falhou (Status: {response.status_code})")
                results[symbol] = False
                
        except Exception as e:
            print(f"❌ {symbol}: Erro - {e}")
            results[symbol] = False
    
    return results

def main():
    """Função principal de teste"""
    if len(sys.argv) < 2:
        print("Uso: python test_het_mock.py <base_url>")
        print("Exemplo: python test_het_mock.py http://localhost:8000")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    print(f"🎭 Testando mock do Heterium em: {base_url}")
    
    # Lista de testes
    tests = [
        ("Health Check", lambda: test_health_with_het(base_url)),
        ("Models Endpoint", lambda: test_models_endpoint(base_url)),
        ("HET Mock", lambda: test_het_mock(base_url)),
        ("Multiple Symbols", lambda: test_multiple_symbols(base_url)),
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
        
        time.sleep(1)  # Pausa entre testes
    
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
        print("🎉 Todos os testes passaram! Mock do HET está funcionando.")
        sys.exit(0)
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs da API.")
        sys.exit(1)

if __name__ == "__main__":
    main() 