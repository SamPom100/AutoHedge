from yfinance.ticker import Ticker

class Stock(Ticker):
    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.option_chain_cache = {}

    def get_option_dates(self):
        return super().options

    def get_calls(self, date: str):
        if date in self.option_chain_cache:
            return self.option_chain_cache[date].calls
        else:
            self.option_chain_cache[date] = super().option_chain(date)
            return self.option_chain_cache[date].calls

    def get_puts(self, date: str):
        if date in self.option_chain_cache:
            return self.option_chain_cache[date].puts
        else:
            self.option_chain_cache[date] = super().option_chain(date)
            return self.option_chain_cache[date].puts
        
    def get_current_price(self):
        return super().info['regularMarketPrice']
    
    def get_expected_moves_straddle(self):
        return {date: self.__get_expected_move_straddle(date) for date in self.get_option_dates()}
    
    def get_expected_moves_strangle(self):
        return {date: self.__get_expected_move_strangle(date) for date in self.get_option_dates()}
    
    def get_expected_moves_all(self):
        straddle = self.get_expected_moves_straddle()
        strangle = self.get_expected_moves_strangle()
        return {date: round((straddle[date] + strangle[date]) / 2, 2) for date in strangle}
    
    def __get_midprice(self, option_chain):
        return round(float((option_chain["ask"] + option_chain["bid"]) / 2), 2)

    def __get_atm_straddle(self, date: str):
        calls = self.get_calls(date)
        puts = self.get_puts(date)
        price = self.get_current_price()
        
        closest_call = calls[calls["strike"] >= price].iloc[0]
        closest_put = puts[puts["strike"] <= price].iloc[-1]
        
        return (self.__get_midprice(closest_call), self.__get_midprice(closest_put))

    def __get_otm_strangle(self, date: str):
        calls = self.get_calls(date)
        puts = self.get_puts(date)
        price = self.get_current_price()
        
        otm_call = calls[calls["strike"] > price].iloc[0]
        otm_put = puts[puts["strike"] < price].iloc[-1]
        
        return (self.__get_midprice(otm_call), self.__get_midprice(otm_put))

    def __get_expected_move_straddle(self, date: str):
        call_price, put_price = self.__get_atm_straddle(date)
        price = self.get_current_price()
        
        return round(100 * ((call_price + put_price) * 0.85) / price, 2)

    def __get_expected_move_strangle(self, date: str):        
        straddle_call, straddle_put = self.__get_atm_straddle(date)
        strangle_call, strangle_put = self.__get_otm_strangle(date)
        
        straddle_value = straddle_call + straddle_put
        strangle_value = strangle_call + strangle_put
        
        price = self.get_current_price()
        
        return round(100 * ((straddle_value + strangle_value) / 2) / price, 2)
