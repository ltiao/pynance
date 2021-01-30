import sys
import click
import requests
import requests_cache
import configparser

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from matplotlib.patches import Rectangle
from pandas.tseries.frequencies import to_offset
from pathlib import Path
from pynance.utils import create_session
from utils import WIDTH, GOLDEN_RATIO, pt_to_in


def create_trades_frame(trades_list):

    trades = pd.DataFrame(trades_list)
    return trades.assign(time=pd.to_datetime(trades.time, unit="ms"),
                         price=pd.to_numeric(trades.price),
                         qty=pd.to_numeric(trades.qty),
                         quoteQty=pd.to_numeric(trades.quoteQty))


@click.command()
@click.argument("symbol")
@click.argument("output_dir", default="figures/",
                type=click.Path(file_okay=False, dir_okay=True))
@click.option("--credentials-file", type=click.File('r'),
              default="scripts/credentials")
@click.option('--transparent', is_flag=True)
@click.option('--context', default="paper")
@click.option('--style', default="ticks")
@click.option('--palette', default="muted")
@click.option('--width', '-w', type=float, default=pt_to_in(WIDTH))
@click.option('--height', '-h', type=float)
@click.option('--aspect', '-a', type=float, default=GOLDEN_RATIO)
@click.option('--dpi', type=float, default=300)
@click.option('--extension', '-e', multiple=True, default=["png"])
def main(symbol, credentials_file, output_dir, transparent, context, style,
         palette, width, height, aspect, dpi, extension):

    # preamble
    if height is None:
        height = width / aspect
    # height *= num_iterations
    # figsize = size(width, aspect)
    figsize = (width, height)

    suffix = f"{width*dpi:.0f}x{height*dpi:.0f}"

    rc = {
        "figure.figsize": figsize,
        "font.serif": ["Times New Roman"],
        "text.usetex": False,
    }
    sns.set(context=context, style=style, palette=palette, font="serif", rc=rc)

    output_path = Path(output_dir).joinpath(symbol)
    output_path.mkdir(parents=True, exist_ok=True)

    config = configparser.ConfigParser()
    config.read_file(credentials_file)

    api_key = config["binance"]["api_key"]
    headers = {"X-MBX-APIKEY": api_key}

    limit = 500
    num_blocks_list = [100, 100]

    s = requests_cache.CachedSession(backend="sqlite", expire=6000)
    # s = requests.Session()
    s.headers.update(headers)

    targets = ["BTC", "ETH"]
    source = "AUD"

    series = {}

    for target, num_blocks in zip(targets, num_blocks_list):

        symbol = ''.join((target, source))

        top_id = None
        frames = []

        for block in range(num_blocks):

            if top_id is None:
                url = "https://api.binance.com/api/v3/trades"
                params = dict(symbol=symbol, limit=limit)
            else:
                url = "https://api.binance.com/api/v3/historicalTrades"
                params = dict(symbol=symbol, limit=limit, fromId=top_id-limit)

            r = s.get(url, params=params)
            trades_list = r.json()

            top_id = trades_list[0]["id"]

            frame = create_trades_frame(trades_list)
            frames.append(frame)

        data = pd.concat(frames, axis="index", ignore_index=True, sort=True) \
                 .set_index("time")
        se = data.resample("15T").price.last()
        series[target] = se

    data = pd.DataFrame(series).dropna(axis="index", how="any").reset_index()

    fig, ax = plt.subplots()

    sns.lineplot(x="ETH", y="BTC", estimator=None, sort=False, data=data, ax=ax)

    plt.tight_layout()
    # fig.autofmt_xdate()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"price_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    # foo = data.groupby("target").resample("15T", on="time").price.last()

    # print(foo)
    # print(foo.reset_index(level="target").pivot(columns="target", values="price"))

    # close = data.resample("1H", on="time")
    # print(close)
    # print(close.pivot(columns="target", values="price"))
    # open_ = data["price"].resample("30T", origin="start").first()
    # close = data["price"].resample("30T", origin="start", label="right").last()

    # low = data["price"].resample("30T", origin="start").min()
    # # low.index = low.index + to_offset("2.5T")

    # high = data["price"].resample("30T", origin="start").max()
    # # high.index = high.index + to_offset("2.5T")

    # fig, ax = plt.subplots()

    # sns.scatterplot(x="time", y="price", marker="x", s=0.5, data=data, alpha=0.2, ax=ax)
    # sns.scatterplot(x="time", y="price", marker="x", data=open_.reset_index(), ax=ax)
    # sns.scatterplot(x="time", y="price", marker="x", data=close.reset_index(), ax=ax)
    # sns.scatterplot(x="time", y="price", marker="+", data=low.reset_index(), ax=ax)
    # sns.scatterplot(x="time", y="price", marker="+", data=high.reset_index(), ax=ax)

    # xs = open_.index.to_pydatetime()
    # ys = open_.to_numpy()

    # us = close.index.to_pydatetime()
    # vs = close.to_numpy()

    # # ax.scatter(xs, ys)

    # for (x, y, u, v, l, h) in zip(xs, ys, us, vs, low.to_numpy(), high.to_numpy()):
    #     color = "tab:green" if v > y else "tab:red"
    #     rect = Rectangle((x, y), u - x, v - y, linewidth=1, edgecolor=color, facecolor="none")
    #     ax.add_patch(rect)

    #     ax.hlines(l, x, u, colors=color)
    #     ax.hlines(h, x, u, colors=color)

    # plt.tight_layout()
    # fig.autofmt_xdate()

    # for ext in extension:
    #     fig.savefig(output_path.joinpath(f"price_{context}_{suffix}.{ext}"),
    #                 dpi=dpi, transparent=transparent)

    # plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
