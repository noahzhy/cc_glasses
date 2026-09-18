import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'outputs','f302_bom');await fs.mkdir(out,{recursive:true});
const data=JSON.parse(await fs.readFile(path.join(root,'evidence/bom_data.json'),'utf8'));
const wb=Workbook.create();const bom=wb.worksheets.add('BOM库存');const cost=wb.worksheets.add('成本比较');const notes=wb.worksheets.add('说明');
function style(s,columns,rows,title,headers){
 s.showGridLines=false;s.getRangeByIndexes(0,0,1,columns).merge();s.getCell(0,0).values=[[title]];
 s.getRangeByIndexes(0,0,1,columns).format={fill:'#183F4B',font:{color:'#FFFFFF',bold:true,size:16},rowHeight:34};
 s.getRangeByIndexes(2,0,1,columns).values=[headers];s.getRangeByIndexes(2,0,1,columns).format={fill:'#DFEEF0',font:{bold:true},rowHeight:32,wrapText:true};
 s.getRangeByIndexes(3,0,rows,columns).format={font:{size:10},rowHeight:40,verticalAlignment:'center',wrapText:true};
 s.getRangeByIndexes(0,0,rows+4,columns).format.columnWidth=17;s.freezePanes.freezeRows(3);
}
style(bom,10,data.bom.length,'EVT E6 F302 R2 | 155 fitted parts', ['立创料号','制造商型号','位号','每板数量','查询库存','10板缺口','10板单价 USD','查询时间 UTC','来源','简要参数说明']);
bom.getRangeByIndexes(3,0,data.bom.length,10).values=data.bom.map(row=>[...row,data.parameters[row[0]]]);
bom.getRange('J:J').format.columnWidth=64;
bom.getRange('B:B').format.columnWidth=30;bom.getRange('C:C').format.columnWidth=45;bom.getRange('H:I').format.columnWidth=30;bom.getRange('G4:G100').setNumberFormat('$0.0000');
for(let i=0;i<data.bom.length;i++)if(data.bom[i][5])bom.getRangeByIndexes(i+3,4,1,2).format.fill='#FFE4BF';
style(cost,13,data.cost.length+2,'同源美元阶梯报价 | 旧 P3 对比 F302', ['料号','型号','旧数量/板','新数量/板','1板旧价','1板新价','10板旧价','10板新价','100板旧价','100板新价','1板节省/板','10板节省/板','100板节省/板']);
cost.getRangeByIndexes(3,0,data.cost.length,10).values=data.cost;
cost.getRange('B:B').format.columnWidth=28;cost.getRange('E:M').setNumberFormat('$0.0000');
for(let i=0;i<data.cost.length;i++){
 const r=i+4,x=data.cost[i];
 for(const [col,a,b] of [['K','E','F'],['L','G','H'],['M','I','J']]) {
  cost.getRange(`${col}${r}`).formulas=[[`=IF(COUNT(${a}${r}:${b}${r})=2,C${r}*${a}${r}-D${r}*${b}${r},IF(C${r}=D${r},0,"报价缺失"))`]];
 }
}
const total=data.cost.length+4;cost.getRange(`A${total}:J${total}`).merge();cost.getRange(`A${total}`).values=[['每板物料差额（旧－新）；USD净用量估算，非采购结算价']];
for(const col of ['K','L','M'])cost.getRange(`${col}${total}`).formulas=[[`=SUM(${col}4:${col}${total-1})`]];
cost.getRange(`A${total}:M${total}`).format={fill:'#DFEEF0',font:{bold:true},rowHeight:40,wrapText:true};
for(const [offset,label,qty,prices] of [[1,'旧 P3 每板物料估算','C',['E','G','I']],[2,'新 F302 每板物料估算','D',['F','H','J']]]){
 const row=total+offset;cost.getRange(`A${row}:J${row}`).merge();cost.getRange(`A${row}`).values=[[label]];
 for(let j=0;j<3;j++)cost.getCell(row-1,10+j).formulas=[[`=SUMPRODUCT(${qty}4:${qty}${total-1},${prices[j]}4:${prices[j]}${total-1})`]];
 cost.getRange(`K${row}:M${row}`).setNumberFormat('$0.0000');cost.getRange(`A${row}:M${row}`).format.rowHeight=32;
}
console.log('Computed totals',JSON.stringify(cost.getRange(`K${total}:M${total+2}`).values));
style(notes,1,data.notes.length,'报价和发布边界',['说明']);notes.getRange('A:A').format.columnWidth=125;notes.getRangeByIndexes(3,0,data.notes.length,1).values=data.notes.map(x=>[x]);notes.getRange('A4:A20').format.rowHeight=48;
console.log((await wb.inspect({kind:'region',sheetId:cost.name,range:`K${total}:M${total}`,maxChars:1500,tableMaxRows:2,tableMaxCols:3})).ndjson);
bom.getRange('H4:H100').setNumberFormat('yyyy-mm-dd hh:mm');
cost.getRange(`E4:M${total+2}`).setNumberFormat('$0.0000');
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(path.join(out,'bom_EVT_E6_F302.xlsx'));await fs.copyFile(path.join(out,'bom_EVT_E6_F302.xlsx'),path.join(root,'bom_EVT_E6_F302.xlsx'));
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'formula error scan'})).ndjson);
console.log((await wb.inspect({kind:'region',sheetId:bom.name,range:'J3:J10',maxChars:1600,tableMaxRows:8,tableMaxCols:1})).ndjson);
for(const s of [bom]){const im=await wb.render({sheetName:s.name,range:'I3:J16',scale:1.5,format:'png'});await fs.writeFile(path.join(out,'parameters_preview.png'),new Uint8Array(await im.arrayBuffer()));}
const footerImage=await wb.render({sheetName:cost.name,range:`A${total-3}:M${total+2}`,scale:1.2,format:'png'});await fs.writeFile(path.join(out,'cost_totals.png'),new Uint8Array(await footerImage.arrayBuffer()));
