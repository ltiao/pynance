import sys
import click
import configparser

import requests, requests_cache
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from matplotlib.patches import Rectangle

from pynance.auth import signed_params
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
    secret_key = config["binance"]["secret_key"]

    # s = requests_cache.CachedSession(backend="sqlite")

    # s = create_session(api_key)

    headers = {"X-MBX-APIKEY": api_key}

    # s = requests_cache.CachedSession(backend="sqlite", ignored_parameters=["timestamp", "signature"])
    s = requests.Session()
    s.headers.update(headers)

    r = s.get("https://api.binance.com/api/v3/avgPrice", params=dict(symbol=symbol))
    avg_price = r.json()
    print(f"Average price in the last {avg_price['mins']} minutes: "
          f"{avg_price['price']}")

    current_price = float(avg_price.get("price"))

    if output_path.joinpath("transactions.csv").exists():

        frame = pd.read_csv(output_path.joinpath("transactions.csv"),
                            index_col=["orderId", "id"])

        print(frame)

    else:

        r = s.get("https://api.binance.com/api/v3/myTrades",
                  params=signed_params(params=dict(symbol=symbol),
                                       secret_key=secret_key))

        frame = create_trades_frame(r.json()).set_index(["orderId", "id"]) \
            .assign(commission=lambda x: pd.to_numeric(x.commission)) \
            .drop(columns=["quoteQty", "isMaker", "isBestMatch"])
        frame.to_csv(output_path.joinpath("transactions.csv"))

        print(frame)

    new_frame = frame.groupby(level="orderId").agg({"time": "last",
                                                    "price": "last",
                                                    "qty": "sum",
                                                    "commission": "sum",
                                                    "commissionAsset": "last",
                                                    "isBuyer": "last"})

    buys = new_frame.query("isBuyer").sort_values(by="time", ascending=True)
    sells = new_frame.query("not isBuyer").sort_values(by="time", ascending=True)

    buys_arr = buys[["price", "qty"]].to_numpy()
    sells_arr = sells[["price", "qty"]].to_numpy()

    print(buys_arr, sells_arr)

    n = len(buys_arr)
    m = len(sells_arr)

    buy_qty_acc = sell_qty_acc = 0.
    i = j = 0

    spill = 0

    fig, ax = plt.subplots()

    while i < n:

        if sell_qty_acc >= buy_qty_acc or j >= m:

            buy_price, buy_qty = buys_arr[i]

            rect = Rectangle((buy_qty_acc, 0.), buy_qty, buy_price, linewidth=0.25,
                             edgecolor="k", facecolor="none")
            ax.add_patch(rect)

            buy_qty_acc += buy_qty
            i += 1
        else:

            if spill <= 0:
                sell_price, sell_qty = sells_arr[j]

                rect = Rectangle((sell_qty_acc, 0.),
                                 sell_qty, sell_price, linewidth=0.25,
                                 edgecolor="tab:red", facecolor="none")
                ax.add_patch(rect)

            rect = Rectangle((sell_qty_acc, buy_price),
                             min(sell_qty, buy_qty_acc-sell_qty_acc),
                             sell_price - buy_price, linewidth=0.25,
                             edgecolor="tab:green", facecolor="tab:green", alpha=0.2)
            ax.add_patch(rect)

            spill = sell_qty_acc + sell_qty - buy_qty_acc

            if spill > 0:
                sell_qty_acc = buy_qty_acc
                sell_qty = spill
            else:
                sell_qty_acc += sell_qty
                j += 1

    # ax.set_xlim(-0.1, 17)
    # ax.set_ylim(-0.1, 1900)

    ax.set_xlim(None, max(buys.qty.sum(), sells.qty.sum()))
    ax.set_ylim(None, max(current_price, buys.price.max(), sells.price.max()))

    ax.axhline(y=current_price)

    plt.tight_layout()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"rectangles_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    # fig, ax = plt.subplots()

    # buy_qty_acc = 0.
    # for index, row in buys.sort_values(by="time", ascending=True).iterrows():

    #     price, quantity = row["price"], row["qty"]

    #     print(row["commissionAsset"])

    #     rect = Rectangle((buy_qty_acc, 0.), quantity, price, linewidth=0.25,
    #                      edgecolor="k", facecolor="none")
    #     ax.add_patch(rect)

    #     buy_qty_acc += row["qty"]

    # sell_qty_acc = 0.
    # for index, row in sells.sort_values(by="time", ascending=True).iterrows():

    #     price, quantity = row["price"], row["qty"]

    #     print(row["commissionAsset"])

    #     rect = Rectangle((sell_qty_acc, 0.), quantity, price, linewidth=0.25,
    #                      linestyle="--", edgecolor="k", facecolor="none")
    #     ax.add_patch(rect)

    #     sell_qty_acc += row["qty"]

    # ax.set_xlim(-0.1, 17)
    # ax.set_ylim(-0.1, 1900)

    # ax.axhline(y=current_price)

    # plt.tight_layout()

    # for ext in extension:
    #     fig.savefig(output_path.joinpath(f"transactions_{context}_{suffix}.{ext}"),
    #                 dpi=dpi, transparent=transparent)

    # plt.show()

    # r = s.get("https://api.binance.com/api/v3/avgPrice", params=dict(symbol=symbol))
    # avg_price = r.json()
    # print(f"Average price in the last {avg_price['mins']} minutes: "
    #       f"{avg_price['price']}")

    # current_price = float(avg_price.get("price"))

    # frame = frame.assign(cost=lambda x: x.qty * x.price,
    #                      value=lambda x: x.qty * current_price,
    #                      delta=lambda x: x.value - x.cost,
    #                      delta_rate=lambda x: x.delta / x.quoteQty,
    #                      delta_pct=lambda x: 100.0 * x.delta_rate,
    #                      relative_qty=lambda x: (-1)**(~x.isBuyer) * x.qty)

    # print(frame.groupby("orderId").sum())
    # print(frame.relative_qty.cumsum())

    # # r = requests.get("https://api.binance.com/api/v3/trades",
    # #                  params=dict(symbol=symbol))
    # # frame = create_trades_frame(r.json())

    # fig, ax = plt.subplots()

    # sns.lineplot(x="time", y="relative_qty", data=frame.relative_qty.cumsum().reset_index(), ax=ax)

    # plt.tight_layout()
    # fig.autofmt_xdate()

    # for ext in extension:
    #     fig.savefig(output_path.joinpath(f"cumulative_{context}_{suffix}.{ext}"),
    #                 dpi=dpi, transparent=transparent)

    # plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
