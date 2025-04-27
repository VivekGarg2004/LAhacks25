import { PinchButton } from './SpectaclesInteractionKit/Components/UI/PinchButton/PinchButton';
import TrackedHand from './SpectaclesInteractionKit/Providers/HandInputData/TrackedHand';
import { SIK } from './SpectaclesInteractionKit/SIK';


@component
export class CallButton extends BaseScriptComponent {
  @input
  private imageURL: string =
    "https://images.ctfassets.net/dwtpq5hdcqjg/5xTThhJ3WhCey7WlEAuL3z/af2e8d8ab18e640a590265233307c146/og.png";

  @input
  private button: PinchButton;

  @input
  private image: Image;


  // Import the RemoteServiceModule and RemoteMediaModule
  private remoteServiceModule: RemoteServiceModule = require('LensStudio:RemoteServiceModule');
  private remoteMediaModule: RemoteMediaModule = require('LensStudio:RemoteMediaModule');


  private leftHand: TrackedHand = SIK.HandInputData.getHand("left");

  // Function called BEFORE the first frame
  onAwake() {
    this.createEvent("OnStartEvent").bind(this.onStart.bind(this));
    this.createEvent("UpdateEvent").bind(this.update.bind(this));
  }

  private onStart() {
    if (!global.deviceInfoSystem.isEditor()) {
      this.button.sceneObject.enabled = false;
    }

    this.leftHand.onHandFound.add(() => {
      print("Left Hand Found");
      this.button.sceneObject.enabled = true;
    });
    this.leftHand.onHandLost.add(() => {
      print("Left Hand Lost");
      this.button.sceneObject.enabled = false;
    });

    this.button.onButtonPinched.add(() => {
      print("Button Pinched");
      this.performHttpRequestLoadImage();
    });
  }

  private update() {
    if (this.leftHand.isTracked()) {
      const buttonTransform = this.button.getTransform();
      const leftHandTransform = this.leftHand.getSceneObject().getTransform();
      buttonTransform.setWorldRotation(leftHandTransform.getWorldRotation());
      this.button
        .getTransform()
        .setWorldPosition(
          this.leftHand
            .getPalmCenter()
            .add(leftHandTransform.back.uniformScale(5))
        );
    }
  }

  private performHttpRequestLoadImage() {
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