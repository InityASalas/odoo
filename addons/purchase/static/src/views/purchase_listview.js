import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { PurchaseDashBoard } from "@purchase/views/purchase_dashboard";
import { PurchaseFileUploader } from "@purchase/components/purchase_file_uploader/purchase_file_uploader";
import { FileUploadListRenderer } from "@account/views/file_upload_list/file_upload_list_renderer";
import { fileUploadListView } from "@account/views/file_upload_list/file_upload_list_view";

export class PurchaseDashBoardRenderer extends FileUploadListRenderer {
    static template = "purchase.ListRenderer";
    static components = Object.assign({}, FileUploadListRenderer.components, { PurchaseDashBoard });
}

export class FileUploadListController extends ListController {
    static template = `purchase.ListView`;
    static components = {
        ...ListController.components,
        PurchaseFileUploader,
    };
}

export const PurchaseDashBoardListView = {
    ...fileUploadListView,
    Controller: FileUploadListController,
    Renderer: PurchaseDashBoardRenderer,
};

registry.category("views").add("purchase_dashboard_list", PurchaseDashBoardListView);
