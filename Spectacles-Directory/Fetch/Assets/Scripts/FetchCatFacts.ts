import Event from "Scripts/Events";

interface CatFact {
  fact: string;
  length: number;
}

const MAX_LENGTH = 93;
const GAME_ID = '0042400103';


@component
export class FetchCatFacts extends BaseScriptComponent {
  private remoteService: RemoteServiceModule = require("LensStudio:RemoteServiceModule");

  private url = "https://1016-24-43-246-45.ngrok-free.app/api/v1/hello";



  catFactReceived: Event<string>;

  onAwake() {
    this.catFactReceived = new Event<string>();
  }

  public getCatFacts() {
    this.remoteService
      .fetch(this.url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })
      .then((response) => {
          if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status} - ${response.statusText}`);
          }
          return response.text();
      })
      .then((text) => {
          if (!text) {
              throw new Error("Empty response body");
          }
          
          try {
              // Parse the JSON response
              const jsonData = JSON.parse(text);
              
              // Handle different response formats
              if (typeof jsonData === 'object') {
                  if (jsonData.fact) {
                      // It's already in the expected format
                      return jsonData as CatFact;
                  } else {
                      // Convert the whole object to string if fact property doesn't exist
                      const factString = JSON.stringify(jsonData);
                      return { fact: factString, length: factString.length } as CatFact;
                  }
              } else if (typeof jsonData === 'string') {
                  // The response is already a string
                  return { fact: jsonData, length: jsonData.length } as CatFact;
              } else {
                  // Force conversion to string for any other type
                  const factString = String(jsonData);
                  return { fact: factString, length: factString.length } as CatFact;
              }
          } catch (e) {
              // If parsing fails, use the raw text as the fact
              return { fact: text, length: text.length } as CatFact;
          }
      })
      .then((data) => {
          this.catFactReceived.invoke(data.fact);
      })
      .catch(failAsync);
  }
}