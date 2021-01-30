import sys
import click
import requests

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from datetime import datetime
from mpl_toolkits.axes_grid1 import make_axes_locatable
from utils import WIDTH, GOLDEN_RATIO, pt_to_in


def create_trades_frame(trades_list):

    trades = pd.DataFrame(trades_list)
    return trades.assign(time=pd.to_datetime(trades.time, unit="ms"),
                         price=pd.to_numeric(trades.price),
                         qty=pd.to_numeric(trades.qty),
                         quoteQty=pd.to_numeric(trades.quoteQty)) \
                 .set_index(["time", "id"])


@click.command()
@click.argument("symbol")
@click.argument("output_dir", default="figures/",
                type=click.Path(file_okay=False, dir_okay=True))
@click.option('--binwidth', '-b', default=1e-4, type=float)
@click.option('--transparent', is_flag=True)
@click.option('--context', default="paper")
@click.option('--style', default="ticks")
@click.option('--palette', default="muted")
@click.option('--width', '-w', type=float, default=pt_to_in(WIDTH))
@click.option('--height', '-h', type=float)
@click.option('--aspect', '-a', type=float, default=GOLDEN_RATIO)
@click.option('--dpi', type=float, default=300)
@click.option('--extension', '-e', multiple=True, default=["png"])
def main(symbol, output_dir, binwidth, transparent, context, style, palette,
         width, height, aspect, dpi, extension):

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
        "text.usetex": True,
    }
    sns.set(context=context, style=style, palette=palette, font="serif", rc=rc)

    output_path = Path(output_dir).joinpath(symbol)
    output_path.mkdir(parents=True, exist_ok=True)

    # r = requests.get("https://api.binance.com/api/v3/ticker/price",
    #                  params=dict(symbol=symbol))
    # print(r.json())

    # r = requests.get("https://api.binance.com/api/v3/avgPrice",
    #                  params=dict(symbol=symbol))
    # avg_price = r.json()
    # print(f"Average price in the last {avg_price['mins']} minutes: {avg_price['price']}")

    r = requests.get("https://api.binance.com/api/v3/trades",
                     params=dict(symbol=symbol))
    frame = create_trades_frame(r.json())

    fig, ax = plt.subplots()

    sns.scatterplot(x="time", y="price", size="qty", data=frame.reset_index(), ax=ax)

    ax.set_xlabel("Price")
    ax.set_ylabel("Quantity")

    plt.tight_layout()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"trades_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    r = requests.get("https://api.binance.com/api/v3/ticker/bookTicker",
                     params=dict(symbol=symbol))
    book_top = r.json()

    bid_price = book_top.get("bidPrice")
    bid_qty = book_top.get("bidQty")
    ask_price = book_top.get("askPrice")
    ask_qty = book_top.get("askQty")

    name = book_top.pop("symbol")
    s = pd.Series(book_top, name=name, dtype=float)

    click.echo(s.to_markdown())

    r = requests.get("https://api.binance.com/api/v3/depth",
                     params=dict(symbol=symbol))
    results = r.json()
    last_update_id = results.get('lastUpdateId')

    t = datetime.now()

    click.echo(f"Last update ID: {last_update_id}")
    frames = {side: pd.DataFrame(data=results[side], columns=["price", "quantity"], dtype=float)
              for side in ["bids", "asks"]}
    frames_list = [frames[side].assign(side=side) for side in frames]
    data = pd.concat(frames_list, axis="index", ignore_index=True, sort=True)

    click.echo(data.groupby("side").price.describe().to_markdown())

    fig, ax = plt.subplots()

    ax.set_title(f"Last update: {t} (ID: {last_update_id})")

    sns.scatterplot(x="price", y="quantity", hue="side", data=data, ax=ax)

    ax.set_xlabel("Price")
    ax.set_ylabel("Quantity")

    plt.tight_layout()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"scatter_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    fig, ax = plt.subplots()

    ax.set_title(f"Last update: {t} (ID: {last_update_id})")

    sns.boxplot(x="price", y="side", data=data, ax=ax)

    ax.set_xlabel("Price")
    # ax.set_ylabel("Quantity")

    plt.tight_layout()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"box_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    # g = sns.displot(x="price", hue="side", kind="hist", rug=True, data=data,
    #                 height=height, aspect=aspect, binwidth=binwidth)
    # for ext in extension:
    #     g.savefig(output_path.joinpath(f"hist_{context}_{suffix}.{ext}"))

    fig, ax = plt.subplots()

    ax.set_title(f"Last update: {t} (ID: {last_update_id})")

    sns.histplot(x="price", hue="side", binwidth=binwidth, data=data, ax=ax)
    sns.rugplot(x="price", hue="side", data=data, ax=ax)

    plt.tight_layout()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"hist_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    fig, ax = plt.subplots()

    ax.set_title(f"Last update: {t} (ID: {last_update_id})")

    sns.histplot(x="price", weights="quantity", hue="side", binwidth=binwidth,
                 data=data, ax=ax)
    sns.scatterplot(x="price", y="quantity", hue="side", data=data, ax=ax)

    ax.set_xlabel("Price")
    ax.set_ylabel("Quantity")

    plt.tight_layout()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"hist_weighted_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    fig, ax = plt.subplots()

    ax.set_title(f"Last update: {t} (ID: {last_update_id})")

    sns.ecdfplot(x="price", weights="quantity", stat="count",
                 complementary=True, data=frames["bids"], ax=ax)
    sns.ecdfplot(x="price", weights="quantity", stat="count",
                 data=frames["asks"], ax=ax)
    sns.scatterplot(x="price", y="quantity", hue="side", data=data, ax=ax)

    ax.set_xlabel("Price")
    ax.set_ylabel("Quantity")

    plt.tight_layout()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"ecdf_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    fig, ax = plt.subplots()

    sns.scatterplot(x="time", y="price", hue="qty", data=frame.reset_index(), ax=ax)

    ax.set_xlabel("Time")
    ax.set_ylabel("Price")

    divider = make_axes_locatable(ax)

    ax_right = divider.append_axes("right", size=0.9, pad=0.1, sharey=ax)

    sns.ecdfplot(y="price", weights="quantity", stat="count",
                 complementary=True, data=frames["bids"], ax=ax_right)
    sns.ecdfplot(y="price", weights="quantity", stat="count",
                 data=frames["asks"], ax=ax_right)
    sns.scatterplot(x="quantity", y="price", hue="side", data=data, ax=ax_right)

    ax_right.set_xlabel("Quantity")
    ax_right.yaxis.set_tick_params(labelleft=False)

    plt.tight_layout()

    for ext in extension:
        fig.savefig(output_path.joinpath(f"trades_{context}_{suffix}.{ext}"),
                    dpi=dpi, transparent=transparent)

    plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
