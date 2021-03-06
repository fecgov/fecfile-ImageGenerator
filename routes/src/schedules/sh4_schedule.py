import os
import pypdftk

from flask import current_app
from os import path
from routes.src.f3x.helper import (
    process_memo_text,
    build_sh_name_date_dict,
    build_memo_page,
)
from routes.src.utils import directory_files


def print_sh4_line(
    f3x_data,
    md5_directory,
    line_number,
    sh4_list,
    page_cnt,
    current_page_num,
    total_no_of_pages,
    image_num=None,
):

    if sh4_list:
        last_page_cnt = 3 if len(sh4_list) % 3 == 0 else len(sh4_list) % 3
        total_fedshare = 0
        total_nonfedshare = 0
        # total_fednonfed_share = 0

        os.makedirs(md5_directory + "SH4/" + line_number, exist_ok=True)
        sh4_infile = current_app.config["FORM_TEMPLATES_LOCATION"].format("SH4")

        for page_num in range(page_cnt):
            current_page_num += 1
            # page_subtotal = 0
            memo_array = []
            last_page = False

            schedule_page_dict = {}
            schedule_page_dict["lineNumber"] = line_number
            schedule_page_dict["pageNo"] = current_page_num
            schedule_page_dict["totalPages"] = total_no_of_pages

            if image_num:
                schedule_page_dict["IMGNO"] = image_num
                image_num += 1

            page_start_index = page_num * 3
            if page_num + 1 == page_cnt:
                last_page = True

            # This call prepares data to render on PDF
            build_sh4_per_page_schedule_dict(
                last_page,
                last_page_cnt,
                page_start_index,
                schedule_page_dict,
                sh4_list,
                memo_array,
            )

            page_fed_subtotal = float(schedule_page_dict["subFedShare"])
            page_nonfed_subtotal = float(schedule_page_dict["subNonFedShare"])
            schedule_page_dict["subTotalFedNonFedShare"] = "{0:.2f}".format(
                page_fed_subtotal + page_nonfed_subtotal
            )

            total_fedshare += page_fed_subtotal
            total_nonfedshare += page_nonfed_subtotal

            if page_cnt == page_num + 1:
                schedule_page_dict["TotalFedShare"] = "{0:.2f}".format(total_fedshare)
                schedule_page_dict["totalNonFedShare"] = "{0:.2f}".format(
                    total_nonfedshare
                )
                schedule_page_dict["TotalFedNonFedShare"] = "{0:.2f}".format(
                    total_fedshare + total_nonfedshare
                )
            schedule_page_dict["committeeName"] = f3x_data["committeeName"]
            sh4_outfile = (
                md5_directory + "SH4/" + line_number + "/page_" + str(page_num) + ".pdf"
            )
            pypdftk.fill_form(sh4_infile, schedule_page_dict, sh4_outfile)

            # Memo text changes and build memo pages and return updated current_page_num
            current_page_num, image_num = build_memo_page(
                memo_array,
                md5_directory,
                line_number,
                current_page_num,
                page_num,
                total_no_of_pages,
                sh4_outfile,
                name="SH4",
                image_num=image_num,
            )

        pypdftk.concat(
            directory_files(md5_directory + "SH4/" + line_number + "/"),
            md5_directory + "SH4/" + line_number + "/all_pages.pdf",
        )
        if path.isfile(md5_directory + "SH4/all_pages.pdf"):
            pypdftk.concat(
                [
                    md5_directory + "SH4/all_pages.pdf",
                    md5_directory + "SH4/" + line_number + "/all_pages.pdf",
                ],
                md5_directory + "SH4/temp_all_pages.pdf",
            )
            os.rename(
                md5_directory + "SH4/temp_all_pages.pdf",
                md5_directory + "SH4/all_pages.pdf",
            )
        else:
            os.rename(
                md5_directory + "SH4/" + line_number + "/all_pages.pdf",
                md5_directory + "SH4/all_pages.pdf",
            )

    return image_num


def build_sh4_per_page_schedule_dict(
    last_page,
    transactions_in_page,
    page_start_index,
    schedule_page_dict,
    sh4_schedules,
    memo_array,
):
    page_fed_subtotal = 0
    page_nonfed_subtotal = 0

    if not last_page:
        transactions_in_page = 3

    for index in range(transactions_in_page):
        schedule_dict = sh4_schedules[page_start_index + index]
        process_memo_text(schedule_dict, "H4", memo_array)
        if schedule_dict["memoCode"] != "X":
            page_fed_subtotal += schedule_dict["federalShare"]
            page_nonfed_subtotal += schedule_dict["nonfederalShare"]
        build_sh_name_date_dict(
            index + 1, page_start_index, schedule_dict, schedule_page_dict
        )

    schedule_page_dict["subFedShare"] = "{0:.2f}".format(page_fed_subtotal)
    schedule_page_dict["subNonFedShare"] = "{0:.2f}".format(page_nonfed_subtotal)
    schedule_page_dict["subTotalFedNonFedShare"] = float(
        schedule_page_dict["subFedShare"]
    ) + float(schedule_page_dict["subNonFedShare"])
