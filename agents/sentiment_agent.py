import os
import requests
from datetime import datetime, timedelta

class SentimentAgent:
    """
    Analiza sentiment de noticias, earnings calendar e insider trades usando Finnhub.
    API gratuita: 60 requests/minuto.
    """
    
    def __init__(self, config):
        self.config = config
        self.sentiment_config = config.get("sentiment", {})
        self.enabled = self.sentiment_config.get("enabled", False)
        self.api_key = os.getenv(self.sentiment_config.get("finnhub_api_key_env", "FINNHUB_API_KEY"))
        self.base_url = "https://finnhub.io/api/v1"
        
        if self.enabled and not self.api_key:
            print("⚠️ Finnhub API key no configurada. Deshabilitando análisis de sentiment.")
            self.enabled = False
        elif self.enabled:
            print("✅ Sentiment Agent habilitado con Finnhub API")
    
    def get_company_news(self, symbol, days_back=7):
        """Obtiene noticias recientes de la empresa."""
        if not self.enabled:
            return []
        
        try:
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/company-news"
            params = {
                'symbol': symbol,
                'from': from_date,
                'to': to_date,
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()[:10]  # Top 10 noticias
            else:
                return []
        except Exception as e:
            print(f"   ⚠️ Error obteniendo noticias de {symbol}: {e}")
            return []
    
    def calculate_sentiment_score(self, news_list):
        """
        Calcula score de sentiment basado en noticias.
        Retorna: score (-1 a +1), negative_count, positive_count
        """
        if not news_list:
            return 0, 0, 0
        
        # Palabras clave positivas/negativas simples
        positive_keywords = ['surge', 'soar', 'beat', 'strong', 'growth', 'profit', 'upgrade', 'buyback', 'deal', 'partnership']
        negative_keywords = ['plunge', 'crash', 'miss', 'weak', 'loss', 'downgrade', 'investigation', 'lawsuit', 'warning', 'decline']
        
        sentiment_scores = []
        negative_count = 0
        positive_count = 0
        
        for news in news_list:
            headline = news.get('headline', '').lower()
            summary = news.get('summary', '').lower()
            text = headline + ' ' + summary
            
            score = 0
            for word in positive_keywords:
                if word in text:
                    score += 1
            for word in negative_keywords:
                if word in text:
                    score -= 1
            
            sentiment_scores.append(score)
            if score < 0:
                negative_count += 1
            elif score > 0:
                positive_count += 1
        
        # Calcular promedio normalizado (-1 a +1)
        avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        normalized_score = max(-1, min(1, avg_score / 3))  # Normalizar
        
        return normalized_score, negative_count, positive_count
    
    def get_earnings_calendar(self, symbol):
        """Verifica si hay earnings próximos."""
        if not self.enabled:
            return None
        
        try:
            url = f"{self.base_url}/calendar/earnings"
            params = {
                'symbol': symbol,
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                earnings = data.get('earningsCalendar', [])
                
                if earnings:
                    # Obtener próximo earnings
                    next_earnings = earnings[0]
                    earnings_date = next_earnings.get('date')
                    
                    if earnings_date:
                        earnings_dt = datetime.strptime(earnings_date, '%Y-%m-%d')
                        days_until = (earnings_dt - datetime.now()).days
                        return {
                            'date': earnings_date,
                            'days_until': days_until
                        }
            return None
        except Exception as e:
            return None
    
    def get_insider_sentiment(self, symbol):
        """Obtiene sentiment de insider trading (compras/ventas)."""
        if not self.enabled:
            return None
        
        try:
            url = f"{self.base_url}/stock/insider-sentiment"
            params = {
                'symbol': symbol,
                'from': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d'),
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    # Sumar compras y ventas
                    total_change = sum(item.get('change', 0) for item in data['data'])
                    total_mspr = sum(item.get('mspr', 0) for item in data['data'])
                    
                    return {
                        'net_change': total_change,
                        'mspr': total_mspr,  # Monthly Share Purchase Ratio
                        'signal': 'bullish' if total_change > 0 else 'bearish' if total_change < 0 else 'neutral'
                    }
            return None
        except Exception as e:
            return None
    
    def analyze_symbol(self, symbol):
        """
        Análisis completo de sentiment para un símbolo.
        Retorna dict con toda la información.
        """
        if not self.enabled:
            return {
                'enabled': False,
                'sentiment_score': 0,
                'passes': True
            }
        
        # 1. Noticias y sentiment
        news = self.get_company_news(symbol)
        sentiment_score, negative_count, positive_count = self.calculate_sentiment_score(news)
        
        # 2. Earnings calendar
        earnings = self.get_earnings_calendar(symbol)
        
        # 3. Insider sentiment
        insider = self.get_insider_sentiment(symbol)
        
        # Decidir si pasa los filtros
        passes = True
        reasons = []
        
        # Filtro 1: Sentiment mínimo
        min_sentiment = self.sentiment_config.get("min_sentiment_score", -0.3)
        if sentiment_score < min_sentiment:
            passes = False
            reasons.append(f"Sentiment muy negativo ({sentiment_score:.2f})")
        
        # Filtro 2: Demasiadas noticias negativas
        max_negative = self.sentiment_config.get("max_negative_news", 3)
        if negative_count > max_negative:
            passes = False
            reasons.append(f"Muchas noticias negativas ({negative_count})")
        
        # Filtro 3: Earnings próximos
        if self.sentiment_config.get("check_earnings_calendar", True) and earnings:
            exclude_days = self.config.get("quality_filters", {}).get("exclude_earnings_days", 7)
            if 0 <= earnings['days_until'] <= exclude_days:
                passes = False
                reasons.append(f"Earnings en {earnings['days_until']} días")
        
        return {
            'enabled': True,
            'symbol': symbol,
            'sentiment_score': round(sentiment_score, 2),
            'news_count': len(news),
            'positive_news': positive_count,
            'negative_news': negative_count,
            'earnings': earnings,
            'insider': insider,
            'passes': passes,
            'reject_reasons': reasons
        }
    
    def filter_symbols(self, symbols):
        """Filtra símbolos basándose en análisis de sentiment."""
        if not self.enabled:
            return symbols, {}
        
        print(f"\n📰 FASE: ANÁLISIS DE SENTIMENT")
        print(f"{'='*50}")
        print(f"Analizando sentiment de {len(symbols)} símbolos...")
        
        approved = []
        sentiment_data = {}
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Analizando {symbol}...")
            
            analysis = self.analyze_symbol(symbol)
            sentiment_data[symbol] = analysis
            
            if analysis['passes']:
                approved.append(symbol)
                score = analysis['sentiment_score']
                emoji = "📈" if score > 0.2 else "📊" if score > -0.2 else "📉"
                print(f"   ✅ {emoji} Sentiment: {score:.2f} | Noticias: {analysis['news_count']}")
                
                if analysis.get('insider'):
                    insider_signal = analysis['insider']['signal']
                    print(f"      💼 Insiders: {insider_signal}")
            else:
                print(f"   ❌ RECHAZADO: {', '.join(analysis['reject_reasons'])}")
            
            # Rate limiting: 60 requests/min = 1 request/segundo
            if i < len(symbols):
                import time
                time.sleep(1.1)
        
        print(f"\n{'='*50}")
        print(f"📊 RESUMEN SENTIMENT:")
        print(f"   ✅ Aprobados: {len(approved)}/{len(symbols)}")
        print(f"   ❌ Rechazados: {len(symbols) - len(approved)}")
        print(f"{'='*50}\n")
        
        return approved, sentiment_data
