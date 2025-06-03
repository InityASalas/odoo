import { expect, test } from "@odoo/hoot";
import { FieldOperator } from "@web/core/utils/field_operator";

test("operator is valid", () => {
    expect(new FieldOperator("+=1", "brol").isValid).toBe(false);
    expect(new FieldOperator("/=0", "float").isValid).toBe(false);
    expect(new FieldOperator("/=0", "int").isValid).toBe(false);
    expect(new FieldOperator("/=0", "monetary").isValid).toBe(false);
    expect(new FieldOperator("%=3", "float").isValid).toBe(true);
    expect(new FieldOperator("%=3.345", "float").isValid).toBe(true);
    expect(new FieldOperator("%=3.345", "int").isValid).toBe(false);
});

test("operations on int", () => {
    const operations = new Map([
        [["/=0"], [false]],
        [["+=1.5"], [false]],
        [["+=1"], [true, 1, "+"]],
        [["-=0"], [true, 0, "-"]],
        [["/=2"], [true, 2, "/"]],
        [["*=4"], [true, 4, "*"]],
        [["%=3"], [true, 3, "%"]],
    ]);
    operations.forEach((result, [operation]) => {
        const op = new FieldOperator(operation, "int");
        expect(op.isValid).toBe(result[0]);
        if (result[0]) {
            expect(op.increment).toBe(result[1]);
            expect(op.operator).toBe(result[2]);
        }
    });
});

test("operations on float or monetary", () => {
    const operations = new Map([
        [["/=0"], [false]],
        [
            ["-=2.65678909876545", "monetary"],
            [true, 2.66, "-"],
        ],
        [
            ["-=2.65678909876545", "float"],
            [true, 2.6567891, "-"],
        ],
        [
            ["/=2,65678909876545", "monetary"],
            [true, 2.66, "/"],
        ],
        [
            ["/=2,65678909876545", "float"],
            [true, 2.6567891, "/"],
        ],
        [["*=PI"], [true, Math.PI, "*"]],
    ]);
    operations.forEach((result, [operation, type = "float"]) => {
        const op = new FieldOperator(operation, type);
        expect(op.isValid).toBe(result[0]);
        if (result[0]) {
            expect(op.increment).toBe(result[1]);
            expect(op.operator).toBe(result[2]);
        }
    });
});
