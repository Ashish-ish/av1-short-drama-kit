"""
CDN Bandwidth and Transcoding Cost Savings Calculator for Vertical Short-Drama Apps.
Calculates data volume reductions (MB/min, TB/month), fleet-level savings,
and net financial return based on the organization's own CDN contract price.
"""

import argparse
import json
import sys
from typing import Dict, Any


def calculate_data_per_minute(bitrate_kbps: float) -> float:
    """Returns megabytes consumed per viewing minute: kbps * 60 / 8 / 1000."""
    return round((bitrate_kbps * 60.0) / 8000.0, 3)


def calculate_savings(
    cdn_price_per_gb: float,
    monthly_egress_tb: float = 0.0,
    monthly_viewing_minutes: float = 0.0,
    eligible_share_pct: float = 40.0,
    av1_saving_pct: float = 45.0,
    hevc_share_pct: float = 45.0,
    hevc_saving_pct: float = 40.0,
    extra_encode_cost_usd: float = 0.0,
    start_rung_kbps_h264: float = 700.0,
) -> Dict[str, Any]:
    """
    Computes comprehensive bandwidth and dollar savings.
    """
    h264_mb_per_min = calculate_data_per_minute(start_rung_kbps_h264)
    av1_kbps = start_rung_kbps_h264 * (1.0 - (av1_saving_pct / 100.0))
    av1_mb_per_min = calculate_data_per_minute(av1_kbps)

    # If monthly viewing minutes is given, compute egress from minutes; otherwise derive minutes from egress
    if monthly_viewing_minutes > 0:
        base_h264_tb = (monthly_viewing_minutes * h264_mb_per_min) / (1024.0 * 1024.0)
    elif monthly_egress_tb > 0:
        base_h264_tb = monthly_egress_tb
        monthly_viewing_minutes = (base_h264_tb * 1024.0 * 1024.0) / h264_mb_per_min
    else:
        # Default example: 1,000,000 viewing minutes
        monthly_viewing_minutes = 1_000_000.0
        base_h264_tb = (monthly_viewing_minutes * h264_mb_per_min) / (1024.0 * 1024.0)

    # Fleet saving formula:
    # Fleet Egress Saving = (Eligible AV1 Share * AV1 Saving) + (Eligible HEVC Share * HEVC Saving)
    av1_fraction = eligible_share_pct / 100.0
    hevc_fraction = hevc_share_pct / 100.0

    av1_tb_saved = base_h264_tb * av1_fraction * (av1_saving_pct / 100.0)
    hevc_tb_saved = base_h264_tb * hevc_fraction * (hevc_saving_pct / 100.0)
    total_tb_saved = av1_tb_saved + hevc_tb_saved
    delivered_tb = max(0.0, base_h264_tb - total_tb_saved)
    fleet_saving_pct = (total_tb_saved / base_h264_tb) * 100.0 if base_h264_tb > 0 else 0.0

    # Dollar calculations
    gb_saved = total_tb_saved * 1024.0
    gross_monthly_cdn_saved = gb_saved * cdn_price_per_gb
    net_monthly_saved = gross_monthly_cdn_saved - extra_encode_cost_usd
    annual_net_saved = net_monthly_saved * 12.0

    return {
        "inputs": {
            "cdn_price_per_gb": cdn_price_per_gb,
            "monthly_viewing_minutes": round(monthly_viewing_minutes, 0),
            "base_h264_monthly_tb": round(base_h264_tb, 2),
            "eligible_av1_share_pct": eligible_share_pct,
            "av1_saving_pct": av1_saving_pct,
            "eligible_hevc_share_pct": hevc_share_pct,
            "hevc_saving_pct": hevc_saving_pct,
            "extra_monthly_encode_cost_usd": extra_encode_cost_usd,
        },
        "per_minute_metrics": {
            "h264_540p_mb_per_min": h264_mb_per_min,
            "av1_540p_mb_per_min": av1_mb_per_min,
            "saved_mb_per_min": round(h264_mb_per_min - av1_mb_per_min, 3),
        },
        "monthly_totals": {
            "delivered_tb_with_adoption": round(delivered_tb, 2),
            "av1_tb_saved": round(av1_tb_saved, 2),
            "hevc_tb_saved": round(hevc_tb_saved, 2),
            "total_tb_saved": round(total_tb_saved, 2),
            "fleet_saving_pct": round(fleet_saving_pct, 1),
            "gross_cdn_saved_usd": round(gross_monthly_cdn_saved, 2),
            "net_monthly_saved_usd": round(net_monthly_saved, 2),
            "net_annual_saved_usd": round(annual_net_saved, 2),
        },
    }


def print_cli_summary(res: Dict[str, Any]) -> None:
    inp = res["inputs"]
    tot = res["monthly_totals"]
    pmin = res["per_minute_metrics"]

    print("=" * 68)
    print("      AV1 ADOPTION KIT: CDN & TRANSCODING SAVINGS CALCULATOR      ")
    print("=" * 68)
    print(f"Inputs:")
    print(f"  • CDN Egress Price:       ${inp['cdn_price_per_gb']:.4f} / GB")
    print(f"  • Monthly Watch Time:     {inp['monthly_viewing_minutes']:,.0f} minutes")
    print(f"  • Baseline Egress:        {inp['base_h264_monthly_tb']:,.2f} TB (H.264)")
    print(f"  • AV1 Eligible Watch:     {inp['eligible_av1_share_pct']:.1f}% (saving {inp['av1_saving_pct']:.1f}%)")
    print(f"  • HEVC Eligible Watch:    {inp['eligible_hevc_share_pct']:.1f}% (saving {inp['hevc_saving_pct']:.1f}%)")
    print(f"  • Extra Compute Cost:     ${inp['extra_monthly_encode_cost_usd']:,.2f} / month")
    print("-" * 68)
    print(f"Data Rates (540x960 Mid Rung):")
    print(f"  • H.264 (700 kbps):       {pmin['h264_540p_mb_per_min']:.2f} MB / minute")
    print(f"  • AV1 (385 kbps):         {pmin['av1_540p_mb_per_min']:.2f} MB / minute")
    print(f"  • Delta per Minute:       {pmin['saved_mb_per_min']:.2f} MB saved / minute on AV1")
    print("-" * 68)
    print(f"Monthly Impact:")
    print(f"  • Total Egress Saved:     {tot['total_tb_saved']:,.2f} TB / month")
    print(f"  • Fleet Delivered Bytes:  {tot['delivered_tb_with_adoption']:,.2f} TB (reduced by {tot['fleet_saving_pct']:.1f}%)")
    print(f"  • Gross CDN Savings:      ${tot['gross_cdn_saved_usd']:,.2f} / month")
    print(f"  • Net Financial Return:   ${tot['net_monthly_saved_usd']:,.2f} / month")
    print(f"  • Projected Annual Return: ${tot['net_annual_saved_usd']:,.2f} / year")
    print("=" * 68)


def main():
    parser = argparse.ArgumentParser(description="AV1 Short-Drama CDN Savings Calculator")
    parser.add_argument("--cdn-price", type=float, default=0.015, help="CDN price per GB in USD (e.g. 0.015 = $15/TB)")
    parser.add_argument("--monthly-tb", type=float, default=100.0, help="Monthly baseline H.264 egress in TB")
    parser.add_argument("--minutes", type=float, default=0.0, help="Monthly viewing minutes (optional, overrides monthly-tb)")
    parser.add_argument("--av1-share", type=float, default=40.0, help="Share of watch time on AV1-eligible devices (percent)")
    parser.add_argument("--av1-saving", type=float, default=45.0, help="Measured AV1 saving at equal VMAF (percent)")
    parser.add_argument("--hevc-share", type=float, default=45.0, help="Share of watch time on HEVC-eligible devices (percent)")
    parser.add_argument("--hevc-saving", type=float, default=40.0, help="Measured HEVC saving at equal VMAF (percent)")
    parser.add_argument("--encode-cost", type=float, default=150.0, help="Additional monthly transcoding compute cost ($)")
    parser.add_argument("--json", action="store_true", help="Output pure JSON format")
    args = parser.parse_args()

    res = calculate_savings(
        cdn_price_per_gb=args.cdn_price,
        monthly_egress_tb=args.monthly_tb,
        monthly_viewing_minutes=args.minutes,
        eligible_share_pct=args.av1_share,
        av1_saving_pct=args.av1_saving,
        hevc_share_pct=args.hevc_share,
        hevc_saving_pct=args.hevc_saving,
        extra_encode_cost_usd=args.encode_cost,
    )

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print_cli_summary(res)


if __name__ == "__main__":
    main()
