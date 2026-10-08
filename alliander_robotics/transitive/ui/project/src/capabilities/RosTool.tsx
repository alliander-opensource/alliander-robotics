// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { CapabilityContext, CapabilityContextProvider } from "@transitive-sdk/utils-web";
import type { ReactNode, RefObject } from "react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import "./card.css";
import { generateJWT } from "./jwt";

const ROS_VERSION = 2;
// Poll interval to pick up new messages
const POLL_INTERVAL_MS = 250;

export interface Subscription {
  topic: string;
  fields: string[];
  callback: (data: any) => void;
}

export interface Publisher {
  topic: string;
  type: string;
}

export interface Service {
  name: string;
  type: string;
}

interface Ros {
  ready: boolean;
  publish: (publisher: Publisher, message: object) => void;
  callService: <Response = unknown>(service: Service, request: object) => Promise<Response>;
}

const notReady = () => {
  throw new Error("ROS is not ready.");
};

const RosContext = createContext<Ros>({
  ready: false,
  publish: notReady,
  callService: () => Promise.reject(new Error("ROS is not ready.")),
});

// Status shown by the RosTool card:
const RosStatusContext = createContext<{ error: string | null; messages: string | null }>({
  error: null,
  messages: null,
});

// Shorthand to use ROS context in other parts of the code:
export const useRos = () => useContext(RosContext);

function latestValue(messages: any, path: string): unknown {
  return path
    .split("/")
    .filter((key) => key !== "")
    .reduce((value: any, key) => value?.[key], messages);
}

// Bridge between RosProvider and the Transitive capability
const RosBridge = ({
  subscriptions,
  apiRef,
  onReadyChange,
  onMessagesChange,
}: {
  subscriptions: Subscription[];
  apiRef: RefObject<any>;
  onReadyChange: (ready: boolean) => void;
  onMessagesChange: (messages: string) => void;
}) => {
  // import the API exposed by the ros-tool capability
  const capability = useContext(CapabilityContext);
  apiRef.current = capability;
  const ready = !!capability.isReady?.();
  const messages = capability.deviceData?.ros?.[ROS_VERSION]?.messages;

  const [_tick, setTick] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => onReadyChange(ready), [ready, onReadyChange]);

  // (Re)subscribe whenever the set of topics changes:
  const topics = subscriptions.map((sub) => sub.topic).join("\n");
  useEffect(() => {
    if (!ready) return;
    const topicList = topics.split("\n").filter((topic) => topic !== "");
    topicList.forEach((topic) => apiRef.current.subscribe(ROS_VERSION, topic));
    return () => topicList.forEach((topic) => apiRef.current.unsubscribe?.(ROS_VERSION, topic));
  }, [ready, topics, apiRef]);

  // Call a subscription's callback whenever one of its field values changes:
  const lastValues = useRef(new Map<string, string>());
  useEffect(() => {
    onMessagesChange(messages ? JSON.stringify(messages, null, 2) : "");

    for (const sub of subscriptions) {
      const values = sub.fields.map((field) => latestValue(messages, sub.topic + field));
      if (values.some((value) => value === null || value === undefined)) continue;

      const key = sub.topic + sub.fields.join();
      const serialized = JSON.stringify(values);
      if (lastValues.current.get(key) === serialized) continue;

      lastValues.current.set(key, serialized);
      sub.callback(values);
    }
  });

  return null;
};

// Single connection to the ros-tool capability
export function RosProvider({
  device,
  subscriptions,
  children,
}: {
  device: string;
  subscriptions: Subscription[];
  children: ReactNode;
}) {
  const [jwtToken, setJwtToken] = useState("");
  const [jwtError, setJwtError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [messages, setMessages] = useState<string | null>(null);
  const apiRef = useRef<any>(null);

  // Generate JWT token on mount
  useEffect(() => {
    generateJWT(device, "@transitive-robotics/ros-tool").then(
      ({ jwtToken: token, jwtError: error }) => {
        setJwtToken(token);
        setJwtError(error);
      },
    );
  }, [device]);

  const publish = useCallback((publisher: Publisher, message: object) => {
    if (!apiRef.current?.isReady?.()) notReady();
    apiRef.current.publish(ROS_VERSION, publisher.topic, publisher.type, message);
  }, []);

  const callService = useCallback(
    <Response,>(service: Service, request: object) =>
      new Promise<Response>((resolve, reject) => {
        if (!apiRef.current?.isReady?.()) {
          reject(new Error("ROS is not ready."));
          return;
        }
        apiRef.current.callService(
          ROS_VERSION,
          service.name,
          service.type,
          request,
          (error: Error, response: Response) => (error ? reject(error) : resolve(response)),
        );
      }),
    [],
  );

  const ros = useMemo(() => ({ ready, publish, callService }), [ready, publish, callService]);
  const status = useMemo(() => ({ error: jwtError, messages }), [jwtError, messages]);

  return (
    <RosContext.Provider value={ros}>
      <RosStatusContext.Provider value={status}>
        {jwtToken && (
          <div hidden>
            <CapabilityContextProvider jwt={jwtToken}>
              <RosBridge
                subscriptions={subscriptions}
                apiRef={apiRef}
                onReadyChange={setReady}
                onMessagesChange={setMessages}
              />
            </CapabilityContextProvider>
          </div>
        )}
        {children}
      </RosStatusContext.Provider>
    </RosContext.Provider>
  );
}

export function RosTool({ device }: { device: string }) {
  const { error, messages } = useContext(RosStatusContext);

  return (
    <div className="card">
      <div className="header">
        <b>ROS Tool ({device})</b>
      </div>
      <div className="widget">
        {error ? (
          <p>Error: {error}</p>
        ) : (
          <div className="capability">
            <pre>{messages || "No messages received."}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
