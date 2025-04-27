import { Interactable } from "./SpectaclesInteractionKit/Components/Interaction/Interactable/Interactable";
import { InteractorEvent } from "./SpectaclesInteractionKit/Core/Interactor/InteractorEvent";
import NativeLogger from "./SpectaclesInteractionKit/Utils/NativeLogger";

const log = new NativeLogger("MyNativeLogger");
// Interaction System https://developers.snap.com/spectacles/spectacles-frameworks/spectacles-interaction-kit/features/interactionsystem
// Instantiate https://developers.snap.com/lens-studio/api/lens-scripting/classes/Built-In.ObjectPrefab.html#instantiateasync or https://developers.snap.com/lens-studio/lens-studio-workflow/prefabs

@component
export class ExampleLensManager extends BaseScriptComponent {

  // Import the RemoteServiceModule and RemoteMediaModule
  private remoteServiceModule: RemoteServiceModule = require('LensStudio:RemoteServiceModule');
  private remoteMediaModule: RemoteMediaModule = require('LensStudio:RemoteMediaModule');

  @input
  @allowUndefined
  @hint("The button that will create the prefab object")
  httpButtonFoRequest: Interactable;

  @input
  imageURL: string =
    "https://images.ctfassets.net/dwtpq5hdcqjg/5xTThhJ3WhCey7WlEAuL3z/af2e8d8ab18e640a590265233307c146/og.png";

  @input
  public image: Image;


  @input
  handReference: SceneObject

  @input
  button: SceneObject




  onAwake() {
    this.createEvent("OnStartEvent").bind(() => {
      this.onStart();
      // your stuff on start 
      log.d("Onstart event triggered");
      print("Onstart event triggered");
    });

    this.createEvent("UpdateEvent").bind(() => {
      this.attachButton();
      // your stuff on update 
      log.d("Update event triggered");
      print("Update event triggered");
    });

  }

  onStart() {

    // HOW TO CREATE CALLBACK FOR BUTTON 
    // Create an event callback function for the create button
    let onTriggerStartCallback = (event: InteractorEvent) => {

      this.performHttpRequestLoadImage()
      // HERE YOUR STUFF ON CLICK 

      log.d("Click event triggered");
      print("Click event triggered");
    };


    // Add the event listener to the create button onInteractorTriggerStart
    this.httpButtonFoRequest.onInteractorTriggerStart(onTriggerStartCallback);

  }


  attachButton() {

    const buttonTransform = this.button.getTransform();
    const leftHandTransform = this.handReference.getTransform();
    buttonTransform.setWorldRotation(leftHandTransform.getWorldRotation());
    this.button.getTransform().setWorldPosition(this.handReference.getTransform().getWorldPosition());
  }


  performHttpRequestLoadImage() {
    const request = RemoteServiceHttpRequest.create();
    request.url = this.imageURL;
    this.remoteServiceModule.performHttpRequest(request, (response) => {
      print("HTTP request completed successfully");
      this.remoteMediaModule.loadResourceAsImageTexture(
        response.asResource(),
        (texture) => {
          print("Texture loaded successfully");
          this.image.mainPass.baseTex = texture;
        },
        (error) => {
          print("Error loading texture: " + error);
        }
      );
    });

  }
}
