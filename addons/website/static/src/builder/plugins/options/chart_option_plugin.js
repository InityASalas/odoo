import { BuilderAction } from "@html_builder/core/core_builder_action_plugin";
import { ChartOption, DATASET_KEY_PREFIX } from "./chart_option";
import { getCSSVariableValue } from "@html_builder/utils/utils_css";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { isCSSColor } from "@web/core/utils/colors";

class ChartOptionPlugin extends Plugin {
    static id = "chartOptionPlugin";
    static dependencies = ["history"];
    resources = {
        builder_options: [
            {
                OptionComponent: ChartOption,
                selector: ".s_chart",
                props: {
                    isPieChart: this.isPieChart,
                    getColor: (color) => this.getColor(color),
                },
            },
        ],
        so_content_addition_selector: [".s_chart"],
        builder_actions: {
            setChartType: new SetChartTypeAction(this),
            addColumn: new AddColumnAction(this),
            removeColumn: new RemoveColumnAction(this),
            addRow: new AddRowAction(this),
            removeRow: new RemoveRowAction(this),
            updateDatasetValue: new UpdateDatasetValueAction(this),
            updateDatasetLabel: new UpdateDatasetLabelAction(this),
            updateLabelName: new UpdateLabelNameAction(this),
            setMinMax: new setMinMaxAction(this),
            colorChange: new ColorChangeAction(this),
        },
    };

    updateDOMData(editingElement, data) {
        editingElement.dataset.data = JSON.stringify(data);
    }

    getData(editingElement) {
        return JSON.parse(editingElement.dataset.data);
    }

    isPieChart(editingElement) {
        return ["pie", "doughnut"].includes(editingElement.dataset.type);
    }

    getMaxValue(editingElement) {
        const datasets = this.getData(editingElement).datasets;
        let dataValues;
        if (!editingElement.dataset.stacked) {
            dataValues = datasets.flatMap((set) => set.data.map((data) => parseInt(data) || 0));
        } else {
            dataValues = datasets.reduce((acc, set) => {
                const data = set.data.map((data) => parseInt(data) || 0);
                return acc.map((value, i) => value + data[i]);
            }, Array(datasets[0].data.length).fill(0));
        }
        return Math.ceil(Math.max(...dataValues) / 5) * 5;
    }

    getColor(color) {
        if (!color) {
            return "";
        }
        return isCSSColor(color)
            ? color
            : getCSSVariableValue(
                  color,
                  this.window.getComputedStyle(this.document.documentElement)
              );
    }

    randomColor() {
        return (
            "#" + ("00000" + ((Math.random() * (1 << 24)) | 0).toString(16)).slice(-6).toUpperCase()
        );
    }
}

class SetChartTypeAction extends BuilderAction {
    isApplied({ editingElement, value }) {
        return editingElement.dataset.type === value;
    }
    apply({ editingElement, value }) {
        editingElement.dataset.type = value;

        const data = this.plugin.getData(editingElement);
        if (this.plugin.isPieChart(editingElement)) {
            if (typeof data.datasets[0].backgroundColor === "string") {
                data.datasets.forEach((dataset) => {
                    dataset.backgroundColor = [dataset.backgroundColor];
                    dataset.borderColor = [dataset.borderColor];
                    for (let i = 1; i < data.labels.length; i++) {
                        dataset.backgroundColor.push(this.plugin.randomColor());
                        dataset.borderColor.push("");
                    }
                });
            }
        } else if (Array.isArray(data.datasets[0].backgroundColor)) {
            data.datasets.forEach((dataset) => {
                dataset.backgroundColor = dataset.backgroundColor[0];
                dataset.borderColor = dataset.borderColor[0];
            });
        }
        this.plugin.updateDOMData(editingElement, data);
    }
}
class AddColumnAction extends BuilderAction {
    apply({ editingElement }) {
        const data = this.plugin.getData(editingElement);
        const fillDatasetArray = (value) => Array(data.labels.length).fill(value);

        const newDataset = {
            key: DATASET_KEY_PREFIX + Date.now(),
            label: "",
            data: fillDatasetArray(0),
            backgroundColor: this.plugin.isPieChart(editingElement)
                ? data.labels.map(() => this.plugin.randomColor())
                : "",
            borderColor: this.plugin.isPieChart(editingElement) ? fillDatasetArray("") : "",
        };
        data.datasets.push(newDataset);
        this.plugin.updateDOMData(editingElement, data);
    }
}
class RemoveColumnAction extends BuilderAction {
    apply({ editingElement, params: { mainParam: key } }) {
        const data = this.plugin.getData(editingElement);
        const toRemoveIndex = data.datasets.findIndex((dataset) => dataset.key === key);
        data.datasets.splice(toRemoveIndex, 1);
        this.plugin.updateDOMData(editingElement, data);
    }
}
class AddRowAction extends BuilderAction {
    apply({ editingElement }) {
        const data = this.plugin.getData(editingElement);
        data.labels.push("");
        data.datasets.forEach((dataset) => {
            dataset.data.push(0);
            if (this.plugin.isPieChart(editingElement)) {
                dataset.backgroundColor.push(this.plugin.randomColor());
                dataset.borderColor.push("");
            }
        });
        this.plugin.updateDOMData(editingElement, data);
    }
}
class RemoveRowAction extends BuilderAction {
    apply({ editingElement, params: { mainParam: labelIndex } }) {
        const data = this.plugin.getData(editingElement);
        data.labels.splice(labelIndex, 1);
        data.datasets.forEach((dataset) => {
            dataset.data.splice(labelIndex, 1);
            if (this.plugin.isPieChart(editingElement)) {
                dataset.backgroundColor.splice(labelIndex, 1);
                dataset.borderColor.splice(labelIndex, 1);
            }
        });
        this.plugin.updateDOMData(editingElement, data);
    }
}
class UpdateDatasetValueAction extends BuilderAction {
    getValue({ editingElement, params: { datasetKey, valueIndex } }) {
        const data = this.plugin.getData(editingElement);
        const targetDataset = data.datasets.find((dataset) => dataset.key === datasetKey);
        return targetDataset?.data[valueIndex] || 0;
    }
    apply({ editingElement, value, params: { datasetKey, valueIndex } }) {
        const data = this.plugin.getData(editingElement);
        const targetDataset = data.datasets.find((dataset) => dataset.key === datasetKey);
        targetDataset.data[valueIndex] = value;
        this.plugin.updateDOMData(editingElement, data);
    }
}
class UpdateDatasetLabelAction extends BuilderAction {
    getValue({ editingElement, params: { mainParam: datasetKey } }) {
        const data = this.plugin.getData(editingElement);
        const targetDataset = data.datasets.find((dataset) => dataset.key === datasetKey);
        return targetDataset?.label;
    }
    apply({ editingElement, value, params: { mainParam: datasetKey } }) {
        const data = this.plugin.getData(editingElement);
        const targetDataset = data.datasets.find((dataset) => dataset.key === datasetKey);
        targetDataset.label = value;
        this.plugin.updateDOMData(editingElement, data);
    }
}

class UpdateLabelNameAction extends BuilderAction {
    getValue({ editingElement, params: { mainParam: labelIndex } }) {
        const data = this.plugin.getData(editingElement);
        return data.labels[labelIndex];
    }
    apply({ editingElement, value, params: { mainParam: labelIndex } }) {
        const data = this.plugin.getData(editingElement);
        data.labels[labelIndex] = value;
        this.plugin.updateDOMData(editingElement, data);
    }
}
class setMinMaxAction extends BuilderAction {
    getValue({ editingElement, params: { mainParam: type } }) {
        if (type === "min") {
            return parseInt(editingElement.dataset.ticksMin) || "";
        }
        if (type === "max") {
            return parseInt(editingElement.dataset.ticksMax) || "";
        }
    }
    apply({ editingElement, value, params: { mainParam: type } }) {
        let minValue, maxValue;
        let noMin = false;
        let noMax = false;
        if (type === "min") {
            minValue = parseInt(value);
            maxValue = parseInt(editingElement.dataset.ticksMax);
        }
        if (type === "max") {
            maxValue = parseInt(value);
            minValue = parseInt(editingElement.dataset.ticksMin);
        }
        if (isNaN(minValue)) {
            noMin = true;
            minValue = 0;
        }

        if (!isNaN(maxValue)) {
            if (maxValue < minValue) {
                [minValue, maxValue] = [maxValue, minValue];
                [noMin, noMax] = [noMax, noMin];
            } else if (maxValue === minValue) {
                minValue = minValue < 0 ? 2 * minValue : 0;
                maxValue = minValue < 0 ? 0 : 2 * maxValue;
            }
        } else {
            noMax = true;
            maxValue = this.plugin.getMaxValue(editingElement);
            // When max value is not given and min value is greater
            // than chart data values
            if (minValue > maxValue) {
                maxValue = minValue;
                [noMin, noMax] = [noMax, noMin];
            }
        }

        if (noMin) {
            delete editingElement.dataset.ticksMin;
        } else {
            editingElement.dataset.ticksMin = minValue;
        }
        if (noMax) {
            delete editingElement.dataset.ticksMax;
        } else {
            editingElement.dataset.ticksMax = maxValue;
        }
    }
}
class ColorChangeAction extends BuilderAction {
    getValue({ editingElement, params: { type, datasetIndex, dataIndex } }) {
        const data = this.plugin.getData(editingElement);
        if (this.plugin.isPieChart(editingElement)) {
            // TODO: shouldn't getColor be done directly in BuilderColorPicker?
            return this.plugin.getColor(data.datasets[datasetIndex]?.[type][dataIndex]);
        } else {
            return this.plugin.getColor(data.datasets[datasetIndex]?.[type]);
        }
    }
    apply({ editingElement, value, params: { type, datasetIndex, dataIndex } }) {
        const data = this.plugin.getData(editingElement);
        if (this.plugin.isPieChart(editingElement)) {
            data.datasets[datasetIndex][type][dataIndex] = value;
        } else {
            data.datasets[datasetIndex][type] = value;
        }
        this.plugin.updateDOMData(editingElement, data);
    }
}

registry.category("website-plugins").add(ChartOptionPlugin.id, ChartOptionPlugin);
