import {
  Injectable,
  Injector,
  EmbeddedViewRef,
  ApplicationRef,
  ComponentRef,
  EnvironmentInjector,
  createComponent
} from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class DomService {
  constructor(
    private appRef: ApplicationRef,
    private injector: Injector,
    private environmentInjector: EnvironmentInjector
  ) { }

  createComponentRef(component: any, extraData = {}) {
    // 1. Create a component reference from the component
    const componentRef = createComponent(component, {
      environmentInjector: this.environmentInjector,
      elementInjector: this.injector
    });

    Object.assign(componentRef.instance, extraData);
    // 2. Attach component to the appRef so that it's inside the ng component tree
    return componentRef;
  }

  attachToView(componentRef) {
    // 2. Attach component to the appRef so that it's inside the ng component tree
    this.appRef.attachView(componentRef.hostView);

    // 3. Get DOM element from component
    const domElem = (componentRef.hostView as EmbeddedViewRef<any>)
      .rootNodes[0] as HTMLElement;

    // 4. Append DOM element to the body
    document.body.appendChild(domElem);
  }

  appendComponentToBody(component: any, extraData = {}) {
    // 1. Create a component reference from the component
    const componentRef = createComponent(component, {
      environmentInjector: this.environmentInjector,
      elementInjector: this.injector
    });

    Object.assign(componentRef.instance, extraData);
    // 2. Attach component to the appRef so that it's inside the ng component tree
    this.appRef.attachView(componentRef.hostView);

    // 3. Get DOM element from component
    const domElem = (componentRef.hostView as EmbeddedViewRef<any>)
      .rootNodes[0] as HTMLElement;

    // 4. Append DOM element to the body
    document.body.appendChild(domElem);

    return componentRef;
  }

  // remove it from the component tree and from the DOM
  detachComponentFromBody(componentRef: ComponentRef<any>) {
    if (componentRef) {
      this.appRef.detachView(componentRef.hostView);
      componentRef.destroy();
    }
  }
}
