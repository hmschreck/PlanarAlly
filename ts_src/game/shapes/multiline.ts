import BoundingRect from "./boundingrect";
import Shape from "./shape";

import { GlobalPoint, LocalPoint } from "../geom";
import { g2lx, g2ly, g2lz } from "../units";
import { getFogColour } from "../utils";

export default class MultiLine extends Shape {
    type = "multiline";
    points: GlobalPoint[] = [];
    size: number;
    fill: string;
    constructor(startPoint: GlobalPoint, points?: GlobalPoint[], size?: number, fill?: string, uuid?: string) {
        super(startPoint, uuid);
        this.points = points || [];
        this.size = size || 3;
        this.fill = fill || "#000";
    }
    asDict() {
        return Object.assign(this.getBaseDict(), {
            size: this.size,
            points: this.points.map(p => ({ x: p.x, y: p.y })),
        });
    }
    getBoundingBox(): BoundingRect {
        let minx: number = this.refPoint.x;
        let maxx: number = this.refPoint.y;
        let miny: number = this.refPoint.x;
        let maxy: number = this.refPoint.y;
        for (const p of this.points) {
            if (p.x < minx) minx = p.x;
            if (p.x > maxx) maxx = p.x;
            if (p.y < miny) miny = p.y;
            if (p.y > maxy) maxy = p.y;
        }
        return new BoundingRect(new GlobalPoint(minx, miny), maxx - minx, maxy - miny);
    }
    draw(ctx: CanvasRenderingContext2D) {
        super.draw(ctx);
        ctx.beginPath();
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.moveTo(g2lx(this.refPoint.x), g2ly(this.refPoint.y));
        for (const p of this.points) ctx.lineTo(g2lx(p.x), g2ly(p.y));
        if (this.fill === "fog") ctx.strokeStyle = getFogColour();
        else ctx.strokeStyle = this.fill;
        ctx.lineWidth = g2lz(this.size);
        ctx.stroke();
    }
    contains(point: GlobalPoint): boolean {
        return this.points.includes(point);
    }

    center(): GlobalPoint;
    center(centerPoint: GlobalPoint): void;
    center(centerPoint?: GlobalPoint): GlobalPoint | void {} // TODO
    getCorner(point: GlobalPoint): string | undefined {
        return "";
    } // TODO
    visibleInCanvas(canvas: HTMLCanvasElement): boolean {
        return true;
    } // TODO
    snapToGrid(): void {}
    resizeToGrid(): void {}
    resize(resizeDir: string, point: LocalPoint): void {}
}
