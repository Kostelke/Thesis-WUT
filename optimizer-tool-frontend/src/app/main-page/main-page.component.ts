import { Component, OnInit } from '@angular/core';
import * as cytoscape from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import { edgeLoadColors } from "./styles";
import { Subscription } from "rxjs";
import { DataHandlingService } from "../api/data-handling.service";
import { StringMap } from '@angular/compiler/src/compiler_facade_interface';
import { ThrowStmt } from '@angular/compiler';


cytoscape.use(coseBilkent);
interface nodePosition {
  x : number,
  y : number,
  linkedToNode: boolean,
}
interface dataStructure {
  description : string,
  value: number | string,
}

@Component({
  selector: 'app-main-page',
  templateUrl: './main-page.component.html',
  styleUrls: ['./main-page.component.scss']
})
export class MainPageComponent implements OnInit {
  private _subscription: Subscription = new Subscription();
  private nodes = [];
  private edges = [];
  private plants = [];
  public index = 0;
  private cy = cytoscape();
  private nodeCollection;
  private edgeCollection;
  private plantCollection;
  public isLabelOpen = false;
  public labelText = "";
  public nodeData: dataStructure[] = [
    {description: "Node Name", value: "testNodeName"},
    {description: "Demand", value: "2103 MW"},
    {description: "Type", value: "block"},
  ]

  public flowData: dataStructure[] = [
    {description: "test1", value: 1},
    {description: "test1", value: 2},
    {description: "test1", value: 3},
    {description: "test1", value: 4},
    {description: "test1", value: 5},
  ];

  public generationData: dataStructure[] = [];
  public labelPosition: nodePosition = {
    x: 0,
    y: 0,  
    linkedToNode: undefined,
};

  public labelHeader = "";
  public labelDescription = "";
  public isPlantBlock = false;


  public disablePageButtons = false;

  constructor(
    private readonly _dataHandlingService: DataHandlingService,
  ) {
  }
  
  ngOnInit(): void {
 
  this.cy = cytoscape({
      container: document.getElementById('cy'),
      layout: {
        name: "cose-bilkent",
      },
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(id)',
            'font-size': '6px',
            'width': '4px',
            'height': '4px',
            // 'background-color': "rgb(1,1,1)",
          }
        },
        {
          selector: ':child',
          style: {
            'label': 'data(id)',
            'font-size': '2px',
            'width': '2px',
            'height': '2px',
            'background-color': "rgb(1,1,1)",
          }
        },
        {
          selector: 'edge',
          style: {
            'label': 'data(value)',
            'font-size': '4px',
            'width': '1px',
          }
        },
        {
          selector: ':child[isWorking = 0]',
          style: {
            'label': 'data(id)',
            'font-size': '2px',
            'width': '2px',
            'height': '2px',
            'background-color': "rgb(255,0,0)",
          },
        },
        {
          selector: ':child[isWorking = 1]',
          style: {
            'label': 'data(id)',
            'font-size': '2px',
            'width': '2px',
            'height': '2px',
            'background-color': "rgb(0,255,0)",
          },
        },

        ...edgeLoadColors
      ]
    });
    // cytoscape.use( cola );
    // this.cy.layout({
    //   name: 'cola',
    // }).run();



    cytoscape.use(coseBilkent);
    this.cy.layout(
      {
        name: 'cose-bilkent',
      }
    ).run();

    this._subscription.add(this._dataHandlingService._resultJSONObservable.subscribe(result => {
      if (result !== undefined) {
        console.log(result);
        if (this.nodes.length === 0) {
          this.nodes = result.nodes;
          this.edges = result.edges;
          this.plants = result.plants;
          this.nodeCollection = this.cy.add(this.nodes);
          this.plantCollection = this.cy.add(this.plants);
          this.edgeCollection = this.cy.add(this.edges);
          this.cy.layout(
            {
              name: 'cose-bilkent',
            }
          ).run();
        } else {
          this.nodes = result.nodes;
          this.edges = result.edges;
          this.plants = result.plants;
          this.updateGraph()
        }
      }
    }));
    this._subscription.add(this._dataHandlingService._loadingObservable.subscribe(x => {
      this.disablePageButtons = x;
    }))
    
    this.cy.on('tap', 'node', function(evt){
      let node = evt.target;
      let message = "";
    
      console.log(node.data("demand"));
    });

    this.cy.on(
      " cxttap ",
      "node",
      evt => {
        this.cy.userZoomingEnabled(false);
          this.prepareDataForDisplay(evt.target.id());
          this.isLabelOpen = true;
          let id = evt.target.id();

          const pan = this.cy.pan();
          const zoom = this.cy.zoom();
          let verticalPadding = 10;
          let pos = this.cy.$id(evt.target.id()).position();
  
          let nodeDimension = this.cy.$id(evt.target.id()).renderedBoundingBox();
          console.log(nodeDimension);
          document.getElementById("cyLabelContainer").style.display = "block";
          let elemWidth = document.getElementById("cyLabelContainer").offsetWidth;
          let elemHeight = document.getElementById("cyLabelContainer").offsetHeight;
  
          let posH = 0;
          let posV = 0;
  
          let renderedX = pos.x * zoom + pan.x + nodeDimension.w /2;
          let renderedY= pos.y * zoom + pan.y + nodeDimension.h /2;
          this.labelPosition.linkedToNode = evt.target.id();
          if(renderedX >= this.cy.width()/2){
              posH = -1;
          }
          if(renderedY >= this.cy.height()/2){
              posV = -1;
          }
          this.labelPosition.x = renderedX + posH * (nodeDimension.w + elemWidth);
          this.labelPosition.y = renderedY + posV * (nodeDimension.h + elemHeight);        
  
          if(this.labelPosition.y <= 0){
              this.labelPosition.y = verticalPadding;
          }
          else if(this.labelPosition.y + elemHeight >= document.getElementById("cy").offsetHeight){
              this.labelPosition.y = document.getElementById("cy").offsetWidth - verticalPadding - elemHeight;
          }
          this.updateLabelPosition();
          this.nodeData[0].value =  this.cy.$id(evt.target.id()).data().id;
          this.nodeData[1].value =  this.cy.$id(evt.target.id()).data().demand;
          this.nodeData[2].value =  this.cy.$id(evt.target.id()).data().type;
         
      });

      this.cy.on("pan", evt => {
        this.cy.userZoomingEnabled(true);
          if(this.labelPosition.linkedToNode){
            document.getElementById("cyLabelContainer").style.display = "none" ;
            this.isLabelOpen = false;
            this.labelPosition.linkedToNode = undefined;
          }
    });

  }

  updateLabelPosition(){
    document.getElementById("cyLabelContainer").style.display = "block";
    let x = this.labelPosition.x;
    let y = this.labelPosition.y;
    document.getElementById("cyLabelContainer").style.transform = `translate(${x}px, ${y}px)`;
}


  private updateGraph() {
    let index = 0;
    this.nodeCollection.forEach(x => {
      x.data('demand', this.nodes[index].data.demand);
      index++;
    })
    index = 0;
    this.edgeCollection.forEach(x => {
      x.data('percentage', this.edges[index].data.percentage);
      x.data('value', this.edges[index].data.value);
      index++;
    })
    index = 0;
    this.plantCollection.forEach(x => {
      x.data('value', this.plants[index].data.value);
      x.data('isWorking', this.plants[index].data.isWorking);
      index++;
    })
    let values = []
    this.plants.forEach(plant => {
      values.push(plant.data.value);
    });
    console.log(values);
  }

  public onNext() {
    this.index++;
    this._dataHandlingService.nextPeriod();
  }

  public onPrev() {
    this.index--;
    this._dataHandlingService.prevPeriod();
  }

  public prepareDataForDisplay(id: string){
    let inflow = [];
    let outflow = [];
    this.edges.forEach(x => {
      if(x.data.target === id){
        if(x.data.value >= 0){
          inflow.push(x);
        } else {
          outflow.push(x);
        }
      };
    });
    this.edges.forEach(x => {
      if(x.data.source === id){
        if(x.data.value >= 0){
          outflow.push(x);
        } else {
          inflow.push(x);
        }
      };
    });

    let node = this.nodes.find( x => x.data.id === id);
    this.labelHeader = node.data.id;
    this.labelDescription ="Energy flowing into the node: \n";
    this.flowData = [];
    inflow.forEach(x => {
      this.flowData.push({ description: x.data.id, value: Math.abs(x.data.value) + " MW"});
    })
    outflow.forEach(x => {
      this.flowData.push({
        description: x.data.id,
        value: -1 * Math.abs(x.data.value) + ' MW',
      });
    });
    this.generationData = [];
    let blocksInPlant = this.plants.filter(element => element.data.parent === id);
    if(blocksInPlant.length > 0){
      this.isPlantBlock = true;
      blocksInPlant.forEach(block => {
      this.generationData.push({
        description: block.data.id,
        value: block.data.value + " MW"
      });
      });
    }
    else{
      this.isPlantBlock = false;
    };
   }
}
