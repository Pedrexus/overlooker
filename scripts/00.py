from poloniex import Poloniex
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    api_key = "AUK84WVE-BULOO9DM-EZHX4W4U-TLZ84995"
    secret_key = b"4295d8a3e89f02c10c0a95af44c0bd9a897ccc8767483db464fbcdb72e82a15b32facc0a3c8326d4f9dc7d9cb7c9b991324eee2c66dab6a61ebe2b231d6b703e"

    polo = Poloniex(api_key, secret_key)

    data = polo.returnChartData('BTC_LTC', period=900, start=1581899459)
    df = pd.DataFrame(data)

    df["date"] = pd.to_datetime(df["date"], unit="s")
    df2 = df.set_index("date")[["close", "weightedAverage"]].astype('float64')

    df2.plot()
    plt.show()
