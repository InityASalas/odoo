function _getSpecificOperators(fieldDef) {
    if (!fieldDef) {
        fieldDef = {};
    }
    const { type, is_property } = fieldDef;

    if (is_property) {
        switch (type) {
            case "many2many":
            case "tags":
                return ["in", "not in"];
            case "many2one":
            case "selection":
                return ["virtual_in", "virtual_not_in"];
        }
    }
    switch (type) {
        case "selection":
            return ["in", "not in"];
        case "char":
        case "text":
        case "html":
        case "many2one":
        case "many2many":
        case "one2many":
            return ["in", "not in", "ilike", "not ilike", "starts_with", "ends_with"];
        case "date":
        case "datetime":
            return [
                "in",
                "not in",
                "today",
                "not_today",
                ">",
                "<",
                "between",
                "is_not_between",
                "next",
                "not_next",
                "last",
                "not_last",
            ];
        case "integer":
        case "float":
        case "monetary":
            return ["in", "not in", ">", "<", "between", "is_not_between", "ilike", "not ilike"];
        case "json":
            return ["virtual_in", "virtual_not_in", "ilike", "not ilike"];
        case "date_option":
        case "time_option":
            return ["in", "not in", ">", "<", "between", "is_not_between"];
        case "datetime_option":
            return ["virtual_in", "virtual_not_in", ">", "<", "between", "is_not_between"];
        default:
            return [];
    }
}

export function getDomainDisplayedOperators(fieldDef) {
    if (!fieldDef) {
        fieldDef = {};
    }
    if (!fieldDef.type) {
        return ["="];
    }
    return [..._getSpecificOperators(fieldDef), "set", "not_set"];
}
