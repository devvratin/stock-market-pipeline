"""CLI runner to sync local Bronze, Silver, and Gold layers to Azure Data Lake."""

from stress.cloud.adls import sync_medallion_to_adls


def main() -> None:
    counts = sync_medallion_to_adls()
    print("Azure Data Lake sync complete:")
    for layer, count in counts.items():
        print(f"  {layer}: {count} file(s) uploaded")


if __name__ == "__main__":
    main()