import { Interactable } from "./SpectaclesInteractionKit/Components/Interaction/Interactable/Interactable";
import { InteractorEvent } from "./SpectaclesInteractionKit/Core/Interactor/InteractorEvent";
import { SIK } from "./SpectaclesInteractionKit/SIK";
import { mix } from "./SpectaclesInteractionKit/Utils/animate";
import NativeLogger from "./SpectaclesInteractionKit/Utils/NativeLogger";

const log = new NativeLogger("MyNativeLogger");
// Interaction System https://developers.snap.com/spectacles/spectacles-frameworks/spectacles-interaction-kit/features/interactionsystem
// Instantiate https://developers.snap.com/lens-studio/api/lens-scripting/classes/Built-In.ObjectPrefab.html#instantiateasync or https://developers.snap.com/lens-studio/lens-studio-workflow/prefabs

@component
export class ExampleLensManager extends BaseScriptComponent {
  /*
    This script handles the instantiation of a prefab when a button is pressed 
    and moves it to a target destination when the left hand pinches. 
    Pinching again while moving will stop movement.
    
    This script will help you learning how to:
    - Use the Interaction System to detect button press and hand gestures
    - Handling awake, start, and update events
    - Instantiate a prefab object
    - Move an object to a target position
    - Use events to trigger actions after a delay
    - Use the mix function to interpolate between two positions
    - Use the NativeLogger class to log messages to the console from the headset (Use the print function to log messages only to the console)
  */

  @input
  @allowUndefined
  @hint("The prefab object we will instantiate when clicking the create button")
  prefabToInstantiate: ObjectPrefab;

  @input
  @allowUndefined
  @hint("The position reference the object will move to on left-hand pinch")
  destinationReference: SceneObject;

  @input
  @allowUndefined
  @hint("The button that will create the prefab object")
  createButton: Interactable;

  @input
  @hint("The delay time in seconds before the instantiated object is destroyed")
  destroyDelay: number = 5;

  @input
  @hint("Speed at which the object moves to the destination on pinch")
  lerpSpeed: number = 0.1;

  // Reference to the left hand input data
  private leftHand = SIK.HandInputData.getHand("left");
  // Reference to the stored instantiated object - we will use this to
  // remember the object we created and move it to the destination
  private latestObject: SceneObject = null;
  // Flag to check if the object is moving
  private isMoving: boolean = false;

  onAwake() {
    this.createEvent("OnStartEvent").bind(() => {
      this.onStart();
      // your stuff on start 
      log.d("Onstart event triggered");
      print("Onstart event triggered");
    });

    this.createEvent("UpdateEvent").bind(() => {
      this.updateObjectMovement();
      // your stuff on update 
      log.d("Update event triggered");
      print("Update event triggered");
    });
  }

  onStart() {
    // HOW TO CREATE A CLLBACK FOR GESTURES
    // Create an event callback function for the left hand pinch down
    let onPinchDownCallback = () => {
      this.onLeftHandPinchDown(); // Call the method that handles pinch down
      log.d("OnPinchDown event triggered"); // Log the event for debugging
      print("OnPinchDown event triggered"); // Log the event for debugging
    };


    // HOW TO CREATE CALLBACK FOR BUTTON 
    // Create an event callback function for the create button
    let onTriggerStartCallback = (event: InteractorEvent) => {
      if (!this.latestObject) {
        // HERE YOUR STUFF ON CLICK 
        this.instantiate();
        log.d("Create button pressed. Instantiating the prefab object.");
        print("Create button pressed. Instantiating the prefab object.");
      } else {
        log.d("Object already instantiated. Not creating a new one.");
        print("Object already instantiated. Not creating a new one.");
      }
    };


    // Add the event listener to the create button onInteractorTriggerStart
    this.createButton.onInteractorTriggerStart(onTriggerStartCallback);
    // Add the event listener to the left hand onPinchDown
    this.leftHand.onPinchDown.add(onPinchDownCallback);
  }

  // Instantiate the prefab object
  instantiate() {
    this.latestObject = this.prefabToInstantiate.instantiate(null);
    this.latestObject.name = "MyNewObject";
    this.latestObject
      .getTransform()
      .setWorldPosition(
        this.destinationReference.getTransform().getWorldPosition()
      );

    let delayedEvent = this.createEvent("DelayedCallbackEvent");
    delayedEvent.bind(() => {
      if (this.latestObject) {
        this.latestObject.destroy();
        log.d(`Object destroyed after ${this.destroyDelay} seconds`);
        print(`Object destroyed after ${this.destroyDelay} seconds`);
        this.latestObject = null;
        this.isMoving = false;
      }
    });

    delayedEvent.reset(this.destroyDelay);
  }

  // Handle left hand pinch down event
  onLeftHandPinchDown() {
    if (!this.latestObject) return;

    if (this.isMoving) {
      // Stop movement if already moving and user pinches again
      this.isMoving = false;
      log.d("Pinch detected while moving. Stopping movement.");
    } else {
      // Start movement if not moving
      log.d("Left hand pinch detected. Moving object to destination...");
      print("Left hand pinch detected. Moving object to destination...");
      this.isMoving = true;
    }
  }

  // Update the object movement to the destination
  updateObjectMovement() {
    if (this.isMoving && this.latestObject) {
      let currentPos = this.latestObject.getTransform().getWorldPosition();
      let targetPos = this.destinationReference
        .getTransform()
        .getWorldPosition();

      let newPos = mix(currentPos, targetPos, this.lerpSpeed);
      this.latestObject.getTransform().setWorldPosition(newPos);
      log.d("Object is moving to destination");
      print("Object is moving to destination");

      if (currentPos.distance(targetPos) < 0.01) {
        this.isMoving = false;
        log.d("Object reached destination. Waiting for next pinch.");
        print("Object reached destination. Waiting for next pinch.");
      }
    }
  }
}